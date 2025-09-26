from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
from filelock import FileLock
from datetime import datetime, timezone

import json

NOTE_PATH = Path("data\\notes.json")
LOCK_PATH = NOTE_PATH.with_suffix(".lock")


@dataclass
class Note:
    userid: str
    username: Optional[str]
    age: Optional[str]
    profilePictureRating: Optional[str]
    message: Optional[str]
    creator: Optional[str]
    createdAt: Optional[str]

    @classmethod
    def from_dict(cls, userid, data: Dict[str, Any] = '', creator = '') -> "Note":
        data = data or {}
        return cls(
            userid=userid,
            username=data.get("username", ""),
            email=data.get("profilePictureRating", ""),
            age=data.get("age", ""),
            message=data.get("message", ""),
            creator=data.get("creator", creator),
            createdAt = data.get("createdAt", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )

    def addMessage(self, message: str):
        if self.message:
            self.message = self.message + f'\n\n{message}'
        else:
            self.message = message

    def changeInfo(self, username=None, age=None, profilePictureRating=None, message=None):
        if username is not None:
            self.username = username
        if age is not None:
            self.age = age
        if profilePictureRating is not None:
            self.profilePictureRating = profilePictureRating
        if message is not None:
            self.message = message


def loadData(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)


def save_db(db: Dict[str, List[Dict[str, Any]]], path: Path = NOTE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.flush()
    tmp.replace(path)


def addMessage(userid: str, message: str, lock_timeout: float = 5.0, creator = ''):
    lock = FileLock(str(LOCK_PATH), timeout=lock_timeout)
    with lock:
        db = loadData(NOTE_PATH)
        userData = db.get(userid)
        if userData is None:
            userObj = Note.from_dict(userid, userData, creator=creator)
        else:
            userObj = Note.from_dict(userid, userData)
        userObj.addMessage(message)
        db[userid] = {
            "userid": userid,
            "username": userObj.username,
            "profilePictureRating": userObj.profilePictureRating,
            "age": userObj.age,
            "creator": userObj.creator,
            "createdAt": userObj.createdAt,
            "message": userObj.message 
        }
        save_db(db)


def viewNote(userid: str):
    lock = FileLock(str(LOCK_PATH))
    with lock:
        db = loadData(NOTE_PATH)
        userData = db.get(userid)
        if userData is None:
            return None

        return userData


def changeInfo(userid: str, username = None, age = None, profilePictureRating=None, message=None, creator = ''):
    updates = {k: v for k, v in {
        "username": username,
        "age": age,
        "profilePictureRating": profilePictureRating,
        "message": message,
    }.items() if v is not None}

    if not updates:
        return

    lock = FileLock(str(LOCK_PATH))
    with lock:
        db = loadData(NOTE_PATH)
        userData = db.get(userid)
        if userData is None:
            userObj = Note.from_dict(userid, userData, creator=creator)
        else:
            userObj = Note.from_dict(userid, userData)
        userObj.changeInfo(**updates)
        db[userid] = {
            "userid": userid,
            "username": userObj.username,
            "profilePictureRating": userObj.profilePictureRating,
            "age": userObj.age,
            "creator": userObj.creator,
            "createdAt": userObj.createdAt,
            "message": userObj.message
        }
        save_db(db)

def removeNote(userid: str, lock_timeout: float = 5.0):
    lock = FileLock(str(LOCK_PATH), timeout=lock_timeout)
    with lock:
        db = loadData(NOTE_PATH)
        if userid in db:
            del db[userid]
            save_db(db)
            return True
        else:
            return False

def sort_key(item):
    parts = item.split(':', 1)
    if len(parts) == 1 or not parts[1]:
        return (1, 0) # keep items with no username at the end
    return (0, parts[1].strip().lower())

def viewNotes(lock_timeout: float = 5.0):
    lock = FileLock(str(LOCK_PATH), timeout=lock_timeout)
    with lock:
        listOfIds = list()
        db = loadData(NOTE_PATH)
        for k, v in db.items():
            name = v.get("username")
            if name:
                listOfIds.append(f'{k}:{v.get("username")}')
            else:
                listOfIds.append(f'{k}:')

        sorted_data = sorted(listOfIds, key=sort_key)

        listOfIds.clear()
        listOfUsernames = list()
        
        for line in sorted_data:
            line: str = line.split(':')
            listOfIds.append(line[0])
            if line[1]:
                listOfUsernames.append(line[1])
            else:
                listOfUsernames.append('-')


        return listOfIds, listOfUsernames

