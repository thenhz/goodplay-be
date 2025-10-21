from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.core.repositories.notification_repository import NotificationRepository

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')


@notification_bp.route('', methods=['GET'])
@auth_required
def get_notifications(current_user):
    """
    Get user notifications (inbox) with pagination and filters.

    Query params:
        - limit: Number of notifications per page (default 20, max 100)
        - offset: Offset for pagination (default 0)
        - read: Filter by read status (true=read, false=unread, omit=all)
        - type: Filter by notification type
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 20)), 100)  # Default 20, max 100
        offset = int(request.args.get('offset', 0))

        # Parse read filter
        read_param = request.args.get('read')
        read_filter = None
        if read_param is not None:
            read_filter = read_param.lower() == 'true'

        # Parse type filter
        type_param = request.args.get('type')

        # Get notifications from repository
        repository = NotificationRepository()

        # Get filtered notifications
        notifications = repository.get_user_notifications(
            user_id=current_user.user_id,
            read=read_filter,
            type=type_param,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination
        total = repository.count_user_notifications(
            user_id=current_user.user_id,
            read=read_filter,
            type=type_param
        )

        # Get unread count
        unread_count = repository.get_unread_count(current_user.user_id)

        # Check if there are more results
        has_more = (offset + limit) < total

        return success_response(
            "NOTIFICATIONS_RETRIEVED_SUCCESS",
            {
                "notifications": [notif.to_dict() for notif in notifications],
                "total": total,
                "unread_count": unread_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            }
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@notification_bp.route('/unread-count', methods=['GET'])
@auth_required
def get_unread_count(current_user):
    """
    Get unread notification count.
    Lightweight endpoint for badge/counter display.
    """
    try:
        repository = NotificationRepository()
        count = repository.get_unread_count(current_user.user_id)

        return success_response(
            "UNREAD_COUNT_RETRIEVED",
            {"unread_count": count}
        )

    except Exception as e:
        current_app.logger.error(f"Error getting unread count: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@notification_bp.route('/read-all', methods=['PUT'])
@auth_required
def mark_all_as_read(current_user):
    """
    Mark all notifications as read.
    Updates read_at timestamp to current time.
    """
    try:
        repository = NotificationRepository()
        updated_count = repository.mark_all_as_read(current_user.user_id)

        current_app.logger.info(
            f"Marked {updated_count} notifications as read for user {current_user.user_id}"
        )

        return success_response(
            "NOTIFICATIONS_MARKED_READ_SUCCESS",
            {"updated_count": updated_count}
        )

    except Exception as e:
        current_app.logger.error(f"Error marking all as read: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@notification_bp.route('/<notification_id>', methods=['PUT'])
@auth_required
def mark_notification_as_read(current_user, notification_id):
    """
    Mark specific notification as read.
    Updates read_at timestamp to current time.
    """
    try:
        repository = NotificationRepository()

        # Get the notification to verify ownership
        notification = repository.get_notification(notification_id, current_user.user_id)
        if not notification:
            return error_response("NOTIFICATION_NOT_FOUND", status_code=404)

        # Mark as read
        if repository.mark_as_read(notification_id, current_user.user_id):
            # Get updated notification
            notification = repository.get_notification(notification_id, current_user.user_id)

            current_app.logger.info(
                f"Notification {notification_id} marked as read by user {current_user.user_id}"
            )

            return success_response(
                "NOTIFICATION_MARKED_READ_SUCCESS",
                {"notification": notification.to_dict()}
            )
        else:
            return error_response("NOTIFICATION_UPDATE_FAILED", status_code=500)

    except Exception as e:
        current_app.logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@notification_bp.route('/<notification_id>', methods=['DELETE'])
@auth_required
def delete_notification(current_user, notification_id):
    """
    Delete specific notification from inbox.
    Warning: This action cannot be undone.
    """
    try:
        repository = NotificationRepository()

        if repository.delete_notification(notification_id, current_user.user_id):
            current_app.logger.info(
                f"Notification {notification_id} deleted by user {current_user.user_id}"
            )
            return success_response("NOTIFICATION_DELETED_SUCCESS")
        else:
            return error_response("NOTIFICATION_NOT_FOUND", status_code=404)

    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}", exc_info=True)
        return error_response("NOTIFICATION_DELETE_FAILED", status_code=500)


@notification_bp.route('', methods=['DELETE'])
@auth_required
def clear_all_notifications(current_user):
    """
    Clear all notifications.
    Delete all notifications for the authenticated user.
    Warning: This action cannot be undone.
    """
    try:
        repository = NotificationRepository()
        count = repository.clear_all_notifications(current_user.user_id)

        current_app.logger.info(
            f"Cleared {count} notifications for user {current_user.user_id}"
        )

        return success_response("NOTIFICATIONS_CLEARED_SUCCESS")

    except Exception as e:
        current_app.logger.error(f"Error clearing notifications: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)