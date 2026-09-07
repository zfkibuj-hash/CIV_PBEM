"""PBEM health checks — plain-language status for players."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.i18n import t
from src.saves import find_save_file

if TYPE_CHECKING:
    from src.config import AppConfig
    from src.gui.app_controller import AppController
    from src.models.game import Game

_LEVEL_RANK = {"ok": 0, "info": 1, "warn": 2, "error": 3}


def healthy_status_text(games: list["Game"], my_name: str) -> str:
  """OK-strip text: whose turn it is, not a generic 'you can play'."""
  mine = [g for g in games if g.history and g.is_my_turn(my_name)]
  if mine:
    return t("health_ok_your_turn")
  waiting: list[str] = []
  seen: set[str] = set()
  for game in games:
    if not game.history or game.is_finished or not game.current_player:
      continue
    who = game.current_player.name
    fold = who.casefold()
    if fold not in seen:
      seen.add(fold)
      waiting.append(who)
  if waiting:
    return t("health_ok_waiting", player=", ".join(waiting))
  return t("health_ok")


@dataclass
class HealthIssue:
  level: str  # ok | info | warn | error
  code: str
  message: str
  hint: str = ""
  game_name: str = ""


@dataclass
class HealthReport:
  issues: list[HealthIssue] = field(default_factory=list)

  @property
  def worst_level(self) -> str:
    if not self.issues:
      return "ok"
    return max(self.issues, key=lambda i: _LEVEL_RANK.get(i.level, 0)).level

  @property
  def has_problems(self) -> bool:
    return self.worst_level in ("warn", "error")

  def summary(self) -> str:
    if self.worst_level == "ok":
      for issue in self.issues:
        if issue.level == "ok" and issue.message:
          return issue.message
      return t("health_ok")
    errors = [i for i in self.issues if i.level == "error"]
    warns = [i for i in self.issues if i.level == "warn"]
    if errors:
      return errors[0].message
    if warns:
      return warns[0].message
    return t("health_ok")

  def lines(self) -> list[str]:
    out: list[str] = []
    for issue in self.issues:
      if issue.level == "ok":
        continue
      line = issue.message
      if issue.hint:
        line += f"\n  → {issue.hint}"
      out.append(line)
    return out


def run_health_check(
    controller: "AppController",
    games: list["Game"],
    *,
    check_remote: bool = True,
) -> HealthReport:
  """Run local + optional remote checks. Returns issues worst-first."""
  config: AppConfig = controller.config
  report = HealthReport()
  my_name = (config.player_name or "").strip()

  if not my_name:
    report.issues.append(HealthIssue(
      "error", "no_nick", t("health_no_nick"),
      t("health_no_nick_hint"),
    ))

  save_path = Path(config.save_path or "")
  if not save_path.exists():
    report.issues.append(HealthIssue(
      "error", "save_missing", t("health_save_missing", path=config.save_path),
      t("health_save_missing_hint"),
    ))

  if not games:
    report.issues.append(HealthIssue(
      "info", "no_games", t("health_no_games"),
      t("health_no_games_hint"),
    ))

  transport_ok = False
  for game in games:
    game_issues = _check_game(controller, game, my_name, check_remote=check_remote)
    report.issues.extend(game_issues)
    if any(i.code == "transport_ok" for i in game_issues):
      transport_ok = True

  if games and check_remote and not transport_ok:
    if not config.is_unlocked:
      report.issues.append(HealthIssue(
        "error", "locked", t("health_locked"),
        t("health_locked_hint"),
      ))

  if not report.has_problems:
    report.issues.insert(0, HealthIssue(
      "ok", "all_ok", healthy_status_text(games, my_name), "",
    ))

  report.issues.sort(key=lambda i: _LEVEL_RANK.get(i.level, 0), reverse=True)
  return report


def _check_game(
    controller: "AppController",
    game: "Game",
    my_name: str,
    *,
    check_remote: bool,
) -> list[HealthIssue]:
  issues: list[HealthIssue] = []
  gname = game.name
  my_game_name = game.get_game_player_name(my_name) if my_name else ""

  if my_name and game.get_player_index(my_game_name) is None:
    issues.append(HealthIssue(
      "error", "not_in_game", t("health_not_in_game", game=gname),
      t("health_not_in_game_hint", nick=my_name),
      game_name=gname,
    ))
    return issues

  install_id = (getattr(controller.config, "install_id", "") or "").strip()
  if my_game_name and install_id:
    other = game.other_install_claim(my_game_name, install_id)
    if other:
      other_nick = (other.get("local_name") or "").strip() or "?"
      issues.append(HealthIssue(
        "warn", "alias_claimed",
        t("health_alias_claimed", game=gname, player=my_game_name, other=other_nick),
        t("health_alias_claimed_hint"),
        game_name=gname,
      ))

  if not game.history:
    issues.append(HealthIssue(
      "error", "not_synced", t("health_not_synced", game=gname),
      t("health_not_synced_hint"),
      game_name=gname,
    ))

  if not game.transport_config or not game.transport_config.get("type"):
    issues.append(HealthIssue(
      "error", "no_transport", t("health_no_transport", game=gname),
      t("health_no_transport_hint"),
      game_name=gname,
    ))
    return issues

  if not check_remote:
    return issues

  transport = controller._create_transport_for_game(game)
  if not transport:
    issues.append(HealthIssue(
      "error", "no_transport", t("health_no_transport", game=gname),
      t("health_no_transport_hint"),
      game_name=gname,
    ))
    return issues

  if not transport.connect():
    issues.append(HealthIssue(
      "error", "transport_fail", t("health_transport_fail", game=gname),
      t("health_transport_fail_hint"),
      game_name=gname,
    ))
    try:
      transport.disconnect()
    except Exception:
      pass
    return issues

  issues.append(HealthIssue("ok", "transport_ok", "", "", game_name=gname))

  try:
    remote_files = transport.list_files(gname)
  except Exception:
    remote_files = []

  if game.is_my_turn(my_name):
    incoming = [
      f for f in remote_files
      if f.endswith(".CivBeyondSwordSave") and game.is_save_for_player(f, my_name)
    ]
    if not incoming:
      issues.append(HealthIssue(
        "warn", "no_remote_save", t("health_no_remote_save", game=gname),
        t("health_no_remote_save_hint"),
        game_name=gname,
      ))
    else:
      latest = sorted(incoming)[-1]
      local = find_save_file(
        latest,
        controller.config.save_path,
        controller.config.get("civ4_save_path", ""),
        controller.config.get("mirror_saves", True),
        game_name=game.name,
      )
      if not local:
        issues.append(HealthIssue(
          "warn", "save_not_local", t("health_save_not_local", game=gname),
          t("health_save_not_local_hint"),
          game_name=gname,
        ))

  try:
    ok, warnings = controller.verify_game_config(game)
    if not ok and warnings:
      issues.append(HealthIssue(
        "warn", "config_mismatch", t("health_config_mismatch", game=gname),
        warnings[0],
        game_name=gname,
      ))
  except Exception:
    pass

  try:
    transport.disconnect()
  except Exception:
    pass

  return issues
