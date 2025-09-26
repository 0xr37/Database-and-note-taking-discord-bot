from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path

import json

 
DB_PATH = Path("data\\data.json")
ITEMS_PATH = Path("data\\itemdetails.json")
 
@dataclass
class User:
    username: str
    userid: int
    age: str
    private: bool
    terminated: bool
    verified: bool
    collectibles: List[str]
    assets: Dict[str, List[str]]
 
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            username=data.get("username", ""),
            userid=data.get("id", 0),
            private=data.get("private", False),
            terminated=data.get("terminated", False),
            verified=data.get("verified", False),
            collectibles=data.get("collectibles") or [],
            assets=data.get("assets") or {},
        )
 
def loadData(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)
 
_db_raw: Dict[str, dict] | None = None # raw version of the db
_users_by_userid: Dict[str, User] | None = None # userid -> userObj
_items: Dict[str, list] | None = None # Dict of all the collectibles
_item_value: Dict[str, int] | None = None # Values of each asset
_name_to_id: Dict[str, str] | None = None # List of names for an asset
_username_to_id: Dict[str, str] # List of ids for any given username

def loadDB():
    global _db_raw, _users_by_userid, _items, _item_value, _name_to_id, _username_to_id
    _db_raw = loadData(DB_PATH)
    _users_by_userid = {}
    _username_to_id = {}
    for userid, userDetails in _db_raw.items():
        userObj = User.from_dict(userDetails)
        _users_by_userid[userid] = userObj
        if _username_to_id.get(userObj.username):
            newList = _username_to_id.get(userObj.username) + [userid]
            _username_to_id[userObj.username.lower()] = newList
        else:
            _username_to_id[userObj.username.lower()] = [userid]

    _items = loadData(ITEMS_PATH).get("items", {})

    _item_value = {}
    _name_to_id = {}

    for item_id, values in _items.items():
        value = values[3] if values[3] != -1 else values[2] # if values[3] is -1 it means you can't buy officially, use resale price instead of msrp
        _item_value[item_id] = value
        for name in values[:2]:
            if name:
                key = name.lower()
                if key not in _name_to_id:
                    _name_to_id[key] = item_id

 
def getValue(asset: str):
    return _item_value.get(str(asset))
 
def findAssetID(asset: str):
    return _name_to_id.get(asset.lower())
 
def findLimiteds(asset: str, verified: bool | None = None):
    loadDB()
    itemID = findAssetID(asset)
 
    if itemID:
        users = list()
        for user in _users_by_userid.values():
            if user.terminated:
                continue

            if itemID not in user.assets:
                continue

            if verified is None or user.verified == verified:
                users.append(user.userid)

        return users
    else:
        return []
 
def getInfo(userid: str):
    loadDB()
    data = _db_raw.get(userid)

    return data
 
 
def findCollectibles(collectible: str, verified: bool | None = None):
    loadDB()
    users = list()
 
    for user in _users_by_userid.values():
        if user.terminated:
            continue
        
        if verified is None or user.verified == verified:
            for x in user.collectibles:
                if x.lower().startswith(collectible.lower()):
                    users.append(user.userid)
                    break
    
    return users
 
def extractParts(lines: list[str], charToSplit: str, index: int):
    parts = list()
 
    index = int(index) - 1

    for line in lines:
        line = line.strip()
        if line:
            newLine = line.split(charToSplit)
            if len(newLine) >= index:
                part = newLine[index]
                parts.append(part)
    
    return '\n'.join(parts)
 
def getLines(userids: list[str]):
    lines = list()
 
    for userid in userids:
        user = _users_by_userid.get(str(userid))
 
        if user:
            if user.terminated == False:
                value = 0
                for limited, amount in user.assets.items():
                    value +=  getValue(limited) * len(amount)
    
                lines.append(f'{user.username}, {user.userid}, {user.age}, {value}, {user.private}, {user.terminated}, {user.verified}')

    new_line = ['username, userid, profilePictureRating, age, private, terminated, verified'] + lines
    return '\n'.join(new_line)

def findUser(username: str):
    loadDB()
    lines = _username_to_id.get(username)
    if lines is None:
        return False
    return '\n'.join(lines)
