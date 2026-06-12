import datetime
import uuid


class Follow:
    def __init__(self, core):
        self.core = core
        self.db = core.orm.use("follow")

    def _now(self):
        return datetime.datetime.now()

    def _row_data(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            data = dict(row)
        elif hasattr(row, "__data__"):
            data = dict(row.__data__)
        else:
            data = {}
        created_at = data.get("created_at")
        if hasattr(created_at, "strftime"):
            data["created_at"] = created_at.strftime("%Y-%m-%d %H:%M:%S")
        return data

    def is_following(self, follower_id, following_id):
        if not follower_id or not following_id:
            return False
        return self.db.get(follower_id=follower_id, following_id=following_id) is not None

    def relation(self, viewer_id, target_id):
        following = self.is_following(viewer_id, target_id)
        follower = self.is_following(target_id, viewer_id)
        return {
            "is_following": following,
            "is_follower": follower,
            "is_mutual": following and follower,
        }

    def follow(self, follower_id, following_id):
        if not follower_id:
            return None, "로그인이 필요합니다."
        if not following_id:
            return None, "팔로우할 사용자가 필요합니다."
        if follower_id == following_id:
            return None, "나 자신은 팔로우할 수 없습니다."
        if self.core.user.get(id=following_id) is None:
            return None, "사용자를 찾을 수 없습니다."

        current = self.db.get(follower_id=follower_id, following_id=following_id)
        if current:
            return self._row_data(current), None

        payload = {
            "id": str(uuid.uuid4()),
            "follower_id": follower_id,
            "following_id": following_id,
            "created_at": self._now(),
        }
        try:
            self.db.insert(payload)
        except Exception:
            current = self.db.get(follower_id=follower_id, following_id=following_id)
            if current:
                return self._row_data(current), None
            return None, "팔로우를 저장하지 못했습니다."
        return self._row_data(payload), None

    def unfollow(self, follower_id, following_id):
        if not follower_id:
            return False, "로그인이 필요합니다."
        if not following_id:
            return False, "언팔로우할 사용자가 필요합니다."
        self.db.delete(follower_id=follower_id, following_id=following_id)
        return True, None

    def following_ids(self, user_id):
        if not user_id:
            return []
        rows = self.db.rows(follower_id=user_id, orderby="created_at", order="DESC")
        return [row.get("following_id") for row in rows if row.get("following_id")]

    def follower_ids(self, user_id):
        if not user_id:
            return []
        rows = self.db.rows(following_id=user_id, orderby="created_at", order="DESC")
        return [row.get("follower_id") for row in rows if row.get("follower_id")]

    def counts(self, user_id):
        if not user_id:
            return {"following_count": 0, "follower_count": 0}
        return {
            "following_count": self.db.count(follower_id=user_id) or 0,
            "follower_count": self.db.count(following_id=user_id) or 0,
        }

    def delete_user(self, user_id):
        if not user_id:
            return
        self.db.delete(follower_id=user_id)
        self.db.delete(following_id=user_id)


Model = Follow
