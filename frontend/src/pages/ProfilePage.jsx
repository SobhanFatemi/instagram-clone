import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getProfile, getMyProfile } from "../api/profiles";
import { listPosts } from "../api/posts";
import {
  blockUser,
  getBlockedUsers,
  getFollowers,
  getFollowing,
  getMutualFollowers,
  unblockUser,
} from "../api/social";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import FollowButton from "../components/FollowButton";
import Modal from "../components/Modal";
import PostGrid from "../components/PostGrid";
import Spinner from "../components/Spinner";
import UserList from "../components/UserList";

export default function ProfilePage() {
  const { username } = useParams();
  const { user: authUser } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [mutual, setMutual] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [isBlocked, setIsBlocked] = useState(false);
  const [working, setWorking] = useState(false);
  const [openList, setOpenList] = useState(null);

  const [posts, setPosts] = useState([]);
  const [postsCount, setPostsCount] = useState(0);
  const [postsNext, setPostsNext] = useState(null);
  const [postsPage, setPostsPage] = useState(1);

  const isMe = profile && authUser && profile.user_id === authUser.id;

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = username ? await getProfile(username) : await getMyProfile();
      setProfile(data);

      const me = profile_is_me(data, authUser);
      const [followerList, followingList] = await Promise.all([
        getFollowers(data.user_id),
        getFollowing(data.user_id),
      ]);
      setFollowers(followerList);
      setFollowing(followingList);

      const followingNow = me
        ? false
        : followerList.some((u) => u.id === authUser.id);

      if (me) {
        setIsFollowing(false);
        setIsBlocked(false);
        setMutual([]);
      } else {
        setIsFollowing(followingNow);
        const [blocked, mutualList] = await Promise.all([
          getBlockedUsers(),
          getMutualFollowers(data.user_id),
        ]);
        setIsBlocked(blocked.some((u) => u.id === data.user_id));
        setMutual(mutualList);
      }

      if (me || !data.is_private || followingNow) {
        const postData = await listPosts({ author: data.user_id, page: 1 });
        setPosts(postData.results);
        setPostsCount(postData.count);
        setPostsNext(postData.next);
        setPostsPage(1);
      } else {
        setPosts([]);
        setPostsCount(0);
        setPostsNext(null);
      }
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setError("This account doesn't exist or is unavailable.");
      } else {
        setError("Could not load this profile.");
      }
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [username, authUser]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleBlock() {
    setWorking(true);
    try {
      await blockUser(profile.user_id);
      await load();
    } finally {
      setWorking(false);
    }
  }

  async function handleUnblock() {
    setWorking(true);
    try {
      await unblockUser(profile.user_id);
      await load();
    } finally {
      setWorking(false);
    }
  }

  async function loadMorePosts() {
    if (!postsNext) return;
    const postData = await listPosts({
      author: profile.user_id,
      page: postsPage + 1,
    });
    setPosts((current) => [...current, ...postData.results]);
    setPostsNext(postData.next);
    setPostsPage((p) => p + 1);
  }

  function handleFollowChange(next) {
    setIsFollowing(next);
    setFollowers((current) => {
      if (next) {
        return [...current, basicSelf(authUser)];
      }
      return current.filter((u) => u.id !== authUser.id);
    });
  }

  if (loading) return <Spinner label="Loading profile..." />;

  if (error) {
    return (
      <div className="rounded-xl border border-neutral-200 bg-white py-16 text-center">
        <p className="text-sm text-neutral-500">{error}</p>
      </div>
    );
  }

  const locked = profile.is_private && !isMe && !isFollowing;

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-6 sm:flex-row sm:items-start sm:gap-10">
        <Avatar
          src={profile.avatar}
          name={profile.username}
          size={120}
          className="mx-auto sm:mx-0"
        />

        <div className="flex-1 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <h2 className="text-xl font-semibold text-neutral-900">
              {profile.username}
            </h2>

            <div className="flex flex-wrap gap-2">
              {isMe ? (
                <>
                  <Link
                    to="/accounts/edit"
                    className="rounded-lg bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200"
                  >
                    Edit profile
                  </Link>
                  <Link
                    to="/saved"
                    className="rounded-lg bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200"
                  >
                    Saved
                  </Link>
                </>
              ) : isBlocked ? (
                <button
                  type="button"
                  onClick={handleUnblock}
                  disabled={working}
                  className="rounded-lg bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200 disabled:opacity-60"
                >
                  Unblock
                </button>
              ) : (
                <>
                  <FollowButton
                    userId={profile.user_id}
                    initialFollowing={isFollowing}
                    onChange={handleFollowChange}
                  />
                  <button
                    type="button"
                    onClick={handleBlock}
                    disabled={working}
                    className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60"
                  >
                    Block
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-8 text-sm">
            <span>
              <span className="font-semibold text-neutral-900">
                {postsCount}
              </span>{" "}
              <span className="text-neutral-500">posts</span>
            </span>
            <button
              type="button"
              onClick={() => followers.length && setOpenList("followers")}
              className="transition hover:text-neutral-500"
            >
              <span className="font-semibold text-neutral-900">
                {followers.length}
              </span>{" "}
              <span className="text-neutral-500">followers</span>
            </button>
            <button
              type="button"
              onClick={() => following.length && setOpenList("following")}
              className="transition hover:text-neutral-500"
            >
              <span className="font-semibold text-neutral-900">
                {following.length}
              </span>{" "}
              <span className="text-neutral-500">following</span>
            </button>
          </div>

          {profile.display_name && (
            <p className="text-sm font-semibold text-neutral-900">
              {profile.display_name}
            </p>
          )}
          {profile.bio && (
            <p className="whitespace-pre-line text-sm text-neutral-700">
              {profile.bio}
            </p>
          )}

          {isBlocked && (
            <p className="text-sm text-neutral-500">
              You blocked this account. Unblock to follow or interact again.
            </p>
          )}

          {!isMe && !isBlocked && mutual.length > 0 && (
            <p className="text-xs text-neutral-500">
              Followed by{" "}
              <span className="font-medium text-neutral-700">
                {mutual.slice(0, 2).map((u) => u.username).join(", ")}
              </span>
              {mutual.length > 2 && ` and ${mutual.length - 2} more`}
            </p>
          )}
        </div>
      </header>

      <div className="border-t border-neutral-200 pt-6">
        {locked ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <LockIcon />
            <p className="text-sm font-semibold text-neutral-800">
              This account is private
            </p>
            <p className="max-w-xs text-sm text-neutral-500">
              Follow this account to see their posts.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <PostGrid
              posts={posts}
              emptyText={isMe ? "Share your first post." : "No posts yet."}
            />
            {postsNext && (
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={loadMorePosts}
                  className="rounded-lg border border-neutral-300 px-5 py-2 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-100"
                >
                  Show more
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {openList && (
        <Modal
          title={openList === "followers" ? "Followers" : "Following"}
          onClose={() => setOpenList(null)}
        >
          <UserList
            users={openList === "followers" ? followers : following}
            currentUserId={authUser.id}
            emptyText="No users to show."
            onItemClick={() => setOpenList(null)}
          />
        </Modal>
      )}
    </div>
  );
}

function profile_is_me(profile, authUser) {
  return Boolean(authUser) && profile.user_id === authUser.id;
}

function basicSelf(authUser) {
  return {
    id: authUser.id,
    username: authUser.username,
    first_name: authUser.first_name,
    last_name: authUser.last_name,
    is_following: false,
  };
}

function LockIcon() {
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="text-neutral-400"
    >
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}
