import { Link } from "react-router-dom";

import Avatar from "./Avatar";
import FollowButton from "./FollowButton";

function fullName(user) {
  return [user.first_name, user.last_name].filter(Boolean).join(" ");
}

export default function UserList({
  users,
  currentUserId,
  emptyText = "No users yet.",
  onItemClick,
  renderAction,
}) {
  if (!users.length) {
    return <p className="px-4 py-8 text-center text-sm text-neutral-500">{emptyText}</p>;
  }

  return (
    <ul className="divide-y divide-neutral-100">
      {users.map((user) => (
        <li key={user.id} className="flex items-center gap-3 px-4 py-3">
          <Link
            to={`/u/${user.username}`}
            onClick={onItemClick}
            className="flex min-w-0 flex-1 items-center gap-3"
          >
            <Avatar name={user.username} size={44} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-neutral-900">
                {user.username}
              </p>
              {fullName(user) && (
                <p className="truncate text-sm text-neutral-500">{fullName(user)}</p>
              )}
            </div>
          </Link>

          {renderAction
            ? renderAction(user)
            : user.id !== currentUserId && (
                <FollowButton
                  userId={user.id}
                  initialFollowing={user.is_following}
                  size="sm"
                />
              )}
        </li>
      ))}
    </ul>
  );
}
