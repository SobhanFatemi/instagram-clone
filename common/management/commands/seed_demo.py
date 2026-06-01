import random
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from PIL import Image

from messaging.models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageRecipientStatus,
)
from posts.models import Comment, Hashtag, Post, PostHashtag, PostLike, PostMedia
from profiles.models import Profile
from social.models import Follow
from stories.models import Story


User = get_user_model()


DEMO_USERS = [
    {
        "username": "alice_w",
        "first_name": "Alice",
        "last_name": "Walker",
        "email": "alice@example.com",
        "display_name": "Alice Walker",
        "bio": "Coffee, code and cats.",
        "color": (244, 114, 182),
    },
    {
        "username": "ben_carter",
        "first_name": "Ben",
        "last_name": "Carter",
        "email": "ben@example.com",
        "display_name": "Ben Carter",
        "bio": "Chasing light and trails.",
        "color": (96, 165, 250),
    },
    {
        "username": "carla_diaz",
        "first_name": "Carla",
        "last_name": "Diaz",
        "email": "carla@example.com",
        "display_name": "Carla Diaz",
        "bio": "Home cook. Plant collector.",
        "color": (52, 211, 153),
    },
    {
        "username": "dan_lee",
        "first_name": "Dan",
        "last_name": "Lee",
        "email": "dan@example.com",
        "display_name": "Dan Lee",
        "bio": "Designer by day, sketching by night.",
        "color": (251, 191, 36),
    },
    {
        "username": "eva_novak",
        "first_name": "Eva",
        "last_name": "Novak",
        "email": "eva@example.com",
        "display_name": "Eva Novak",
        "bio": "Film photography and old towns.",
        "color": (167, 139, 250),
    },
    {
        "username": "sam_okoro",
        "first_name": "Sam",
        "last_name": "Okoro",
        "email": "sam@example.com",
        "display_name": "Sam Okoro",
        "bio": "City streets after dark.",
        "color": (248, 113, 113),
    },
]

CAPTIONS = [
    "Golden hour somewhere quiet. #sunset #photography",
    "New recipe, no regrets. #food #homecooking",
    "Trail done, legs gone. #hiking #weekend",
    "Studio light practice. #portrait #art",
    "City never sleeps. #street #night",
    "Morning brew ritual. #coffee #slowliving",
    "Beach day reset. #ocean #travel",
    "Desk setup finally clean. #workspace #tech",
    "Old town wandering. #architecture #europe",
    "Fresh prints drying. #film #analog",
    "Plant corner is thriving. #plants #home",
    "Late night sketching. #drawing #creative",
]

COMMENTS = [
    "Love this!",
    "Incredible shot.",
    "Where is this?",
    "Total goals.",
    "So clean.",
    "Need the recipe.",
    "Adding this to my list.",
    "This made my day.",
]

STORY_TEXTS = [
    "Out exploring today",
    "Behind the scenes",
    "Quick coffee break",
]


def make_image(color, size=640):
    image = Image.new("RGB", (size, size), color)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    return ContentFile(buffer.getvalue(), name="seed.jpg")


class Command(BaseCommand):
    help = "Create demo users, profiles, follows, posts, stories and conversations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        if options["flush"]:
            self.flush_demo_data()

        users = self.create_users()
        self.create_follows(users)
        posts = self.create_posts(users)
        self.create_engagement(users, posts)
        self.create_stories(users)
        self.create_conversations(users)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(users)} demo users and {len(posts)} posts. "
                "Log in by requesting an OTP for any demo email (e.g. alice@example.com)."
            )
        )

    def flush_demo_data(self):
        usernames = [item["username"] for item in DEMO_USERS]
        User.objects.filter(username__in=usernames).delete()
        Conversation.objects.filter(participants__isnull=True).delete()
        self.stdout.write("Removed existing demo data.")

    def create_users(self):
        users = []

        for item in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=item["username"],
                defaults={
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "email": item["email"],
                    "is_email_verified": True,
                },
            )

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.display_name = item["display_name"]
            profile.bio = item["bio"]

            if not profile.avatar:
                profile.avatar.save("avatar.jpg", make_image(item["color"], size=320), save=False)

            profile.save()
            users.append(user)

        return users

    def create_follows(self, users):
        count = len(users)

        for index, follower in enumerate(users):
            following = [
                users[(index + 1) % count],
                users[(index + 2) % count],
            ]

            for target in following:
                Follow.objects.get_or_create(follower=follower, following=target)

    def create_posts(self, users):
        posts = []
        caption_index = 0

        for user in users:
            if user.posts.exists():
                posts.extend(user.posts.all())
                continue

            for _ in range(2):
                caption = CAPTIONS[caption_index % len(CAPTIONS)]
                caption_index += 1

                post = Post.objects.create(author=user, caption=caption)
                PostMedia.objects.create(
                    post=post,
                    media=make_image(self.user_color(user)),
                    media_type=PostMedia.TYPE_IMAGE,
                    sort_order=0,
                )
                self.set_hashtags(post, caption)
                posts.append(post)

        return posts

    def set_hashtags(self, post, caption):
        for word in caption.split():
            if not word.startswith("#"):
                continue

            name = word.lstrip("#").lower()
            if not name:
                continue

            hashtag, _ = Hashtag.objects.get_or_create(name=name)
            PostHashtag.objects.get_or_create(post=post, hashtag=hashtag)

    def create_engagement(self, users, posts):
        for post in posts:
            others = [user for user in users if user.id != post.author_id]
            likers = random.sample(others, k=random.randint(1, 3))

            for liker in likers:
                PostLike.objects.get_or_create(user=liker, post=post)

            if random.random() < 0.7:
                commenter = random.choice(others)
                Comment.objects.create(
                    user=commenter,
                    post=post,
                    content=random.choice(COMMENTS),
                )

            post.like_count = post.likes.count()
            post.comment_count = post.comments.filter(deleted_at__isnull=True).count()
            post.save(update_fields=["like_count", "comment_count", "updated_at"])

    def create_stories(self, users):
        for index, user in enumerate(users[:3]):
            if user.stories.filter(expires_at__gt=timezone.now()).exists():
                continue

            Story.objects.create(
                user=user,
                media_type=Story.TYPE_IMAGE,
                file=make_image(self.user_color(user)),
                text=STORY_TEXTS[index % len(STORY_TEXTS)],
                expires_at=timezone.now() + timedelta(hours=24),
            )

    def create_conversations(self, users):
        self.create_direct_conversation(users[0], users[1], [
            (users[0], "Hey! Did you see the new posts?"),
            (users[1], "Yes, the sunset one is unreal."),
            (users[0], "Right? Sending you the spot later."),
        ])

        self.create_group_conversation(
            "Weekend Crew",
            users[0],
            [users[0], users[2], users[3]],
            [
                (users[0], "Planning a hike this weekend, who is in?"),
                (users[2], "Count me in!"),
                (users[3], "I will bring snacks."),
            ],
        )

    def create_direct_conversation(self, user_a, user_b, messages):
        existing = (
            Conversation.objects.filter(
                conversation_type=Conversation.TYPE_DIRECT,
                participants__user=user_a,
            )
            .filter(participants__user=user_b)
            .first()
        )
        if existing:
            return

        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            created_by=user_a,
        )
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=conversation, user=user_a),
            ConversationParticipant(conversation=conversation, user=user_b),
        ])

        for sender, text in messages:
            self.send_message(conversation, sender, text)

    def create_group_conversation(self, title, creator, members, messages):
        if Conversation.objects.filter(
            conversation_type=Conversation.TYPE_GROUP,
            title=title,
        ).exists():
            return

        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_GROUP,
            title=title,
            created_by=creator,
        )
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(
                conversation=conversation,
                user=member,
                is_admin=(member.id == creator.id),
            )
            for member in members
        ])

        for sender, text in messages:
            self.send_message(conversation, sender, text)

    def send_message(self, conversation, sender, text):
        now = timezone.now()

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            message_type=Message.TYPE_TEXT,
            text=text,
        )

        conversation.last_message_at = now
        conversation.save(update_fields=["last_message_at", "updated_at"])

        recipient_ids = (
            conversation.participants
            .exclude(user=sender)
            .values_list("user_id", flat=True)
        )
        MessageRecipientStatus.objects.bulk_create([
            MessageRecipientStatus(message=message, user_id=recipient_id, delivered_at=now)
            for recipient_id in recipient_ids
        ])

    def user_color(self, user):
        for item in DEMO_USERS:
            if item["username"] == user.username:
                return item["color"]
        return (148, 163, 184)
