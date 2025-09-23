from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from ..services.achievement_engine import AchievementEngine
from ..services.progress_tracker import ProgressTracker
from ..services.badge_service import BadgeService
from ..repositories.achievement_repository import AchievementRepository

achievement_bp = Blueprint('achievements', __name__)

def get_achievement_engine():
    """Get achievement engine instance"""
    return AchievementEngine()

def get_progress_tracker():
    """Get progress tracker instance"""
    return ProgressTracker()

def get_badge_service():
    """Get badge service instance"""
    return BadgeService()

def get_achievement_repo():
    """Get achievement repository instance"""
    return AchievementRepository()


@achievement_bp.route('', methods=['GET'])
@auth_required
def get_achievements(current_user):
    """Get all available achievements"""
    try:
        achievement_repo = get_achievement_repo()
        category = request.args.get('category')

        if category:
            achievements = achievement_repo.find_achievements_by_category(category)
        else:
            achievements = achievement_repo.find_active_achievements()

        achievements_data = [achievement.to_response_dict() for achievement in achievements]

        return success_response("ACHIEVEMENTS_RETRIEVED_SUCCESS", achievements_data)

    except Exception as e:
        current_app.logger.error(f"Get achievements error: {str(e)}")
        return error_response("ACHIEVEMENTS_RETRIEVAL_FAILED", status_code=500)


@achievement_bp.route('/user', methods=['GET'])
@auth_required
def get_user_achievements(current_user):
    """Get user's achievements with progress"""
    try:
        achievement_repo = get_achievement_repo()
        user_id = current_user.get_id()
        completed_only = request.args.get('completed_only', 'false').lower() == 'true'

        user_achievements = achievement_repo.find_user_achievements(user_id, completed_only)

        # Enrich with achievement definitions
        enriched_achievements = []
        for user_achievement in user_achievements:
            achievement_def = achievement_repo.find_achievement_by_id(user_achievement.achievement_id)
            if achievement_def:
                user_ach_data = user_achievement.to_response_dict()
                user_ach_data['achievement_definition'] = achievement_def.to_response_dict()
                enriched_achievements.append(user_ach_data)

        return success_response("USER_ACHIEVEMENTS_RETRIEVED_SUCCESS", enriched_achievements)

    except Exception as e:
        current_app.logger.error(f"Get user achievements error: {str(e)}")
        return error_response("USER_ACHIEVEMENTS_RETRIEVAL_FAILED", status_code=500)


@achievement_bp.route('/user/progress', methods=['GET'])
@auth_required
def get_user_progress_summary(current_user):
    """Get comprehensive progress summary for user"""
    try:
        progress_tracker = get_progress_tracker()
        user_id = current_user.get_id()

        success, message, progress_data = progress_tracker.get_user_progress_summary(user_id)

        if success:
            return success_response("USER_PROGRESS_RETRIEVED_SUCCESS", progress_data)
        else:
            return error_response("USER_PROGRESS_RETRIEVAL_FAILED")

    except Exception as e:
        current_app.logger.error(f"Get user progress error: {str(e)}")
        return error_response("USER_PROGRESS_RETRIEVAL_FAILED", status_code=500)


@achievement_bp.route('/user/recommendations', methods=['GET'])
@auth_required
def get_achievement_recommendations(current_user):
    """Get achievement recommendations for user"""
    try:
        progress_tracker = get_progress_tracker()
        user_id = current_user.get_id()

        success, message, recommendations = progress_tracker.get_achievement_recommendations(user_id)

        if success:
            return success_response("ACHIEVEMENT_RECOMMENDATIONS_RETRIEVED_SUCCESS", recommendations)
        else:
            return error_response("ACHIEVEMENT_RECOMMENDATIONS_FAILED")

    except Exception as e:
        current_app.logger.error(f"Get achievement recommendations error: {str(e)}")
        return error_response("ACHIEVEMENT_RECOMMENDATIONS_FAILED", status_code=500)


@achievement_bp.route('/claim-reward', methods=['POST'])
@auth_required
def claim_achievement_reward(current_user):
    """Claim reward for completed achievement"""
    try:
        achievement_repo = get_achievement_repo()
        data = request.get_json()
        if not data:
            return error_response("ACHIEVEMENT_CLAIM_DATA_REQUIRED")

        achievement_id = data.get('achievement_id', '').strip()
        if not achievement_id:
            return error_response("ACHIEVEMENT_ID_REQUIRED")

        user_id = current_user.get_id()

        # Check if achievement is completed and not claimed
        user_achievement = achievement_repo.find_user_achievement(user_id, achievement_id)
        if not user_achievement:
            return error_response("ACHIEVEMENT_NOT_FOUND")

        if not user_achievement.is_completed:
            return error_response("ACHIEVEMENT_NOT_COMPLETED")

        if user_achievement.reward_claimed:
            return error_response("ACHIEVEMENT_REWARD_ALREADY_CLAIMED")

        # Get achievement definition for reward amount
        achievement_def = achievement_repo.find_achievement_by_id(achievement_id)
        if not achievement_def:
            return error_response("ACHIEVEMENT_DEFINITION_NOT_FOUND")

        # Claim the reward
        success = achievement_repo.claim_achievement_reward(user_id, achievement_id)

        if success:
            reward_data = {
                "achievement_id": achievement_id,
                "reward_credits": achievement_def.calculate_final_reward(),
                "badge_rarity": achievement_def.badge_rarity
            }
            return success_response("ACHIEVEMENT_REWARD_CLAIMED_SUCCESS", reward_data)
        else:
            return error_response("ACHIEVEMENT_REWARD_CLAIM_FAILED")

    except Exception as e:
        current_app.logger.error(f"Claim achievement reward error: {str(e)}")
        return error_response("ACHIEVEMENT_REWARD_CLAIM_FAILED", status_code=500)


@achievement_bp.route('/badges/user', methods=['GET'])
@auth_required
def get_user_badges(current_user):
    """Get user's badge collection"""
    try:
        badge_service = get_badge_service()
        user_id = current_user.get_id()
        visible_only = request.args.get('visible_only', 'false').lower() == 'true'

        success, message, badges_data = badge_service.get_user_badges(user_id, visible_only)

        if success:
            return success_response("USER_BADGES_RETRIEVED_SUCCESS", badges_data)
        else:
            return error_response("USER_BADGES_RETRIEVAL_FAILED")

    except Exception as e:
        current_app.logger.error(f"Get user badges error: {str(e)}")
        return error_response("USER_BADGES_RETRIEVAL_FAILED", status_code=500)


@achievement_bp.route('/badges/user/collection', methods=['GET'])
@auth_required
def get_user_badge_collection(current_user):
    """Get comprehensive badge collection with statistics"""
    try:
        badge_service = get_badge_service()
        user_id = current_user.get_id()

        success, message, collection_data = badge_service.get_user_badge_collection(user_id)

        if success:
            return success_response("USER_BADGE_COLLECTION_RETRIEVED_SUCCESS", collection_data)
        else:
            return error_response("USER_BADGE_COLLECTION_RETRIEVAL_FAILED")

    except Exception as e:
        current_app.logger.error(f"Get user badge collection error: {str(e)}")
        return error_response("USER_BADGE_COLLECTION_RETRIEVAL_FAILED", status_code=500)


@achievement_bp.route('/impact-score', methods=['GET'])
@auth_required
def get_impact_score(current_user):
    """Get user's impact score based on achievements"""
    try:
        achievement_engine = get_achievement_engine()
        user_id = current_user.get_id()

        success, message, impact_score = achievement_engine.calculate_impact_score(user_id)

        if success:
            score_data = {
                "impact_score": impact_score,
                "calculated_at": current_app.extensions.get('achievement_engine', {}).get('last_calculation')
            }
            return success_response("IMPACT_SCORE_CALCULATED_SUCCESS", score_data)
        else:
            return error_response("IMPACT_SCORE_CALCULATION_FAILED")

    except Exception as e:
        current_app.logger.error(f"Get impact score error: {str(e)}")
        return error_response("IMPACT_SCORE_CALCULATION_FAILED", status_code=500)


@achievement_bp.route('/leaderboard', methods=['GET'])
@auth_required
def get_achievement_leaderboard(current_user):
    """Get achievement leaderboard"""
    try:
        achievement_repo = get_achievement_repo()
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 entries

        leaderboard = achievement_repo.get_leaderboard(limit)

        return success_response("ACHIEVEMENT_LEADERBOARD_RETRIEVED_SUCCESS", leaderboard)

    except Exception as e:
        current_app.logger.error(f"Get achievement leaderboard error: {str(e)}")
        return error_response("ACHIEVEMENT_LEADERBOARD_RETRIEVAL_FAILED", status_code=500)