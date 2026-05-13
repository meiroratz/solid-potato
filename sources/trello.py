import requests
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
import config


BASE_URL = "https://api.trello.com/1"


def _params(**extra) -> dict:
    return {"key": config.TRELLO_API_KEY, "token": config.TRELLO_TOKEN, **extra}


@dataclass
class TrelloAction:
    board_name: str
    card_name: str
    action_type: str
    member: str
    date: datetime
    list_name: Optional[str] = None
    comment: Optional[str] = None

    @property
    def human_action(self) -> str:
        mapping = {
            "createCard": "created card",
            "updateCard": "moved/updated card",
            "commentCard": "commented on",
            "deleteCard": "deleted card",
            "addMemberToCard": "joined card",
            "removeMemberFromCard": "left card",
            "archiveCard": "archived card",
        }
        return mapping.get(self.action_type, self.action_type)


def fetch() -> list[TrelloAction]:
    if not config.TRELLO_API_KEY or not config.TRELLO_TOKEN:
        return []

    since = (datetime.now(timezone.utc) - timedelta(days=config.TRELLO_ACTIVITY_DAYS)).isoformat()

    boards_resp = requests.get(f"{BASE_URL}/members/me/boards", params=_params(filter="open"))
    boards_resp.raise_for_status()
    boards = boards_resp.json()

    if config.TRELLO_BOARDS:
        boards = [b for b in boards if b["name"] in config.TRELLO_BOARDS]

    actions: list[TrelloAction] = []

    for board in boards:
        board_id = board["id"]
        board_name = board["name"]

        act_resp = requests.get(
            f"{BASE_URL}/boards/{board_id}/actions",
            params=_params(
                filter="createCard,updateCard,commentCard,deleteCard",
                since=since,
                limit=50,
            ),
        )
        if not act_resp.ok:
            continue

        for act in act_resp.json():
            data = act.get("data", {})
            card = data.get("card", {})
            member_creator = act.get("memberCreator", {})

            actions.append(TrelloAction(
                board_name=board_name,
                card_name=card.get("name", "(unnamed card)"),
                action_type=act["type"],
                member=member_creator.get("fullName", member_creator.get("username", "Someone")),
                date=datetime.fromisoformat(act["date"].replace("Z", "+00:00")),
                list_name=data.get("list", {}).get("name") or data.get("listAfter", {}).get("name"),
                comment=data.get("text") if act["type"] == "commentCard" else None,
            ))

    actions.sort(key=lambda a: a.date, reverse=True)
    return actions
