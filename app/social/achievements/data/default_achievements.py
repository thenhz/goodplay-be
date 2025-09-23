from ..models.achievement import Achievement

def get_default_achievements():
    """
    Get default achievement definitions to be created in the database

    Returns:
        List[Achievement]: List of default achievements
    """

    achievements = []

    # Gaming Achievements
    achievements.extend([
        Achievement(
            achievement_id="rookie_player",
            name="Rookie Player",
            description="Complete your first game session",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 1
            },
            badge_rarity=Achievement.COMMON,
            reward_credits=10,
            icon_url="/static/badges/rookie_player.png"
        ),

        Achievement(
            achievement_id="game_explorer",
            name="Game Explorer",
            description="Try 5 different games",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": "game_diversity",
                "target_value": 5
            },
            badge_rarity=Achievement.RARE,
            reward_credits=25,
            icon_url="/static/badges/game_explorer.png"
        ),

        Achievement(
            achievement_id="score_master",
            name="Score Master",
            description="Achieve a top 10 score in any game",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SCORE,
                "target_value": 10,
                "comparison": "lte"  # rank <= 10
            },
            badge_rarity=Achievement.EPIC,
            reward_credits=50,
            icon_url="/static/badges/score_master.png"
        ),

        Achievement(
            achievement_id="consistency_king",
            name="Consistency King",
            description="Play for 7 consecutive days",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.CONSECUTIVE_DAYS,
                "target_value": 7
            },
            badge_rarity=Achievement.RARE,
            reward_credits=30,
            icon_url="/static/badges/consistency_king.png"
        ),

        Achievement(
            achievement_id="tournament_champion",
            name="Tournament Champion",
            description="Win a weekly tournament",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": "tournament_victory",
                "target_value": 1
            },
            badge_rarity=Achievement.LEGENDARY,
            reward_credits=100,
            icon_url="/static/badges/tournament_champion.png"
        ),

        Achievement(
            achievement_id="session_warrior",
            name="Session Warrior",
            description="Complete 50 game sessions",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 50
            },
            badge_rarity=Achievement.EPIC,
            reward_credits=75,
            icon_url="/static/badges/session_warrior.png"
        )
    ])

    # Social Achievements
    achievements.extend([
        Achievement(
            achievement_id="social_butterfly",
            name="Social Butterfly",
            description="Add 10 friends",
            category=Achievement.SOCIAL,
            trigger_conditions={
                "type": Achievement.SOCIAL_FRIEND,
                "target_value": 10
            },
            badge_rarity=Achievement.RARE,
            reward_credits=20,
            icon_url="/static/badges/social_butterfly.png"
        ),

        Achievement(
            achievement_id="helper",
            name="Helper",
            description="Help 5 friends with challenges",
            category=Achievement.SOCIAL,
            trigger_conditions={
                "type": "help_provided",
                "target_value": 5
            },
            badge_rarity=Achievement.RARE,
            reward_credits=25,
            icon_url="/static/badges/helper.png"
        ),

        Achievement(
            achievement_id="community_star",
            name="Community Star",
            description="Receive 100 likes on activities",
            category=Achievement.SOCIAL,
            trigger_conditions={
                "type": Achievement.SOCIAL_LIKE,
                "target_value": 100
            },
            badge_rarity=Achievement.EPIC,
            reward_credits=40,
            icon_url="/static/badges/community_star.png"
        ),

        Achievement(
            achievement_id="first_friend",
            name="First Friend",
            description="Add your first friend",
            category=Achievement.SOCIAL,
            trigger_conditions={
                "type": Achievement.SOCIAL_FRIEND,
                "target_value": 1
            },
            badge_rarity=Achievement.COMMON,
            reward_credits=5,
            icon_url="/static/badges/first_friend.png"
        ),

        Achievement(
            achievement_id="popular_player",
            name="Popular Player",
            description="Receive 25 likes on your activities",
            category=Achievement.SOCIAL,
            trigger_conditions={
                "type": Achievement.SOCIAL_LIKE,
                "target_value": 25
            },
            badge_rarity=Achievement.RARE,
            reward_credits=15,
            icon_url="/static/badges/popular_player.png"
        )
    ])

    # Impact Achievements
    achievements.extend([
        Achievement(
            achievement_id="first_donation",
            name="First Donation",
            description="Make your first donation",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": Achievement.DONATION_COUNT,
                "target_value": 1
            },
            badge_rarity=Achievement.COMMON,
            reward_credits=15,
            icon_url="/static/badges/first_donation.png"
        ),

        Achievement(
            achievement_id="generous_heart",
            name="Generous Heart",
            description="Donate €50 total",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": Achievement.DONATION_AMOUNT,
                "target_value": 5000  # €50 in cents
            },
            badge_rarity=Achievement.RARE,
            reward_credits=30,
            icon_url="/static/badges/generous_heart.png"
        ),

        Achievement(
            achievement_id="social_impact",
            name="Social Impact",
            description="Donate to 10 different ONLUS",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": "onlus_diversity",
                "target_value": 10
            },
            badge_rarity=Achievement.EPIC,
            reward_credits=60,
            icon_url="/static/badges/social_impact.png"
        ),

        Achievement(
            achievement_id="monthly_donor",
            name="Monthly Donor",
            description="Donate for 6 consecutive months",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": "monthly_donation_streak",
                "target_value": 6
            },
            badge_rarity=Achievement.LEGENDARY,
            reward_credits=120,
            icon_url="/static/badges/monthly_donor.png"
        ),

        Achievement(
            achievement_id="big_giver",
            name="Big Giver",
            description="Donate €200 total",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": Achievement.DONATION_AMOUNT,
                "target_value": 20000  # €200 in cents
            },
            badge_rarity=Achievement.EPIC,
            reward_credits=80,
            icon_url="/static/badges/big_giver.png"
        ),

        Achievement(
            achievement_id="regular_supporter",
            name="Regular Supporter",
            description="Make 25 donations",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": Achievement.DONATION_COUNT,
                "target_value": 25
            },
            badge_rarity=Achievement.RARE,
            reward_credits=35,
            icon_url="/static/badges/regular_supporter.png"
        )
    ])

    return achievements


def initialize_default_achievements(achievement_repo):
    """
    Initialize default achievements in the database

    Args:
        achievement_repo: AchievementRepository instance
    """
    try:
        default_achievements = get_default_achievements()

        created_count = 0
        for achievement in default_achievements:
            # Check if achievement already exists
            existing = achievement_repo.find_achievement_by_id(achievement.achievement_id)
            if not existing:
                achievement_repo.create_achievement(achievement)
                created_count += 1

        print(f"Initialized {created_count} default achievements")
        return True

    except Exception as e:
        print(f"Error initializing default achievements: {str(e)}")
        return False