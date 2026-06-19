from sqlalchemy.orm import Session
from models import Notification, Team, TeamMember, User
from schemas import NotificationCreate
from typing import Optional, Dict, Any

def create_notification(db: Session, notification: NotificationCreate) -> Notification:
    db_notif = Notification(
        receiver_username=notification.receiver_username,
        sender_username=notification.sender_username,
        text=notification.text,
        type=notification.type,
        need_operation=notification.need_operation,
        metadata=notification.metadata,
        is_read=False
    )
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif

def get_user_notifications(db: Session, username: str):
    return db.query(Notification).filter(Notification.receiver_username == username).order_by(Notification.created_at.desc()).all()

def mark_notification_read(db: Session, notif_id: int, username: str) -> Optional[Notification]:
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.receiver_username == username).first()
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif

def mark_all_read(db: Session, username: str):
    db.query(Notification).filter(Notification.receiver_username == username, Notification.is_read == False).update({"is_read": True})
    db.commit()

def clear_notifications(db: Session, username: str):
    db.query(Notification).filter(Notification.receiver_username == username).delete()
    db.commit()

def accept_notification(db: Session, notif_id: int, username: str):
    from crud import add_team_member, update_team_member_role, transfer_team_ownership
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.receiver_username == username).first()
    if not notif:
        return None, "通知不存在"
    if notif.is_read:
        return None, "通知已处理"
    if not notif.need_operation:
        notif.is_read = True
        db.commit()
        return notif, "已标记已读"

    meta = notif.metadata or {}
    if notif.type == "team_invitation":
        team_id = meta.get("teamId")
        role = meta.get("role", "member")
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None, "团队不存在"
        if db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.username == username).first():
            return None, "您已在该团队中"
        # 加入团队（Owner 为邀请人，实际使用 team.owner_username 作为操作者）
        member, error = add_team_member(db, team_id, username, team.owner_username)
        if error:
            return None, error
        if role == "admin":
            update_team_member_role(db, team_id, username, "admin", team.owner_username)
        notif.is_read = True
        db.commit()
        if notif.sender_username:
            create_notification(db, NotificationCreate(
                receiver_username=notif.sender_username,
                sender_username=username,
                text=f"{username} 已接受加入团队「{team.name}」的邀请。",
                type="team_invitation_accepted",
                need_operation=False,
                metadata={"teamId": team_id, "teamTitle": team.name}
            ))
        return notif, "已接受邀请"

    elif notif.type == "owner_transfer_request":
        team_id = meta.get("teamId")
        old_owner = meta.get("oldOwner")
        new_owner = meta.get("newOwner")
        if username != new_owner:
            return None, "无权接受此转让"
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None, "团队不存在"
        if team.owner_username != old_owner:
            return None, "原Owner已变更"
        success, error = transfer_team_ownership(db, team_id, username, old_owner)
        if not success:
            return None, error
        notif.is_read = True
        db.commit()
        if old_owner:
            create_notification(db, NotificationCreate(
                receiver_username=old_owner,
                sender_username=username,
                text=f"{username} 已接受团队「{team.name}」的 Owner 转让请求。",
                type="owner_transfer_accepted",
                need_operation=False,
                metadata={"teamId": team_id, "teamTitle": team.name}
            ))
        return notif, "已接受转让"
    else:
        notif.is_read = True
        db.commit()
        return notif, "已确认"

def reject_notification(db: Session, notif_id: int, username: str):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.receiver_username == username).first()
    if not notif:
        return None, "通知不存在"
    if notif.is_read:
        return None, "通知已处理"
    if not notif.need_operation:
        notif.is_read = True
        db.commit()
        return notif, "已标记已读"
    meta = notif.metadata or {}
    if notif.type == "team_invitation":
        team_id = meta.get("teamId")
        team = db.query(Team).filter(Team.id == team_id).first()
        notif.is_read = True
        db.commit()
        if notif.sender_username:
            create_notification(db, NotificationCreate(
                receiver_username=notif.sender_username,
                sender_username=username,
                text=f"{username} 已拒绝加入团队「{team.name if team else ''}」的邀请。",
                type="team_invitation_rejected",
                need_operation=False,
                metadata={"teamId": team_id}
            ))
        return notif, "已拒绝邀请"
    elif notif.type == "owner_transfer_request":
        team_id = meta.get("teamId")
        team = db.query(Team).filter(Team.id == team_id).first()
        notif.is_read = True
        db.commit()
        if notif.sender_username:
            create_notification(db, NotificationCreate(
                receiver_username=notif.sender_username,
                sender_username=username,
                text=f"{username} 已拒绝团队「{team.name if team else ''}」的 Owner 转让请求。",
                type="owner_transfer_rejected",
                need_operation=False,
                metadata={"teamId": team_id}
            ))
        return notif, "已拒绝转让"
    else:
        notif.is_read = True
        db.commit()
        return notif, "已拒绝"