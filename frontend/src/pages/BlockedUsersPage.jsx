import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getBlockedUsers, unblockUser } from "../api/social";
import Spinner from "../components/Spinner";
import UserList from "../components/UserList";

export default function BlockedUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setUsers(await getBlockedUsers());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleUnblock(userId) {
    setBusyId(userId);
    try {
      await unblockUser(userId);
      setUsers((current) => current.filter((u) => u.id !== userId));
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <Spinner label="Loading..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/accounts/edit"
          className="text-sm text-neutral-500 transition hover:text-neutral-800"
        >
          &larr; Back
        </Link>
        <h2 className="text-xl font-semibold text-neutral-900">Blocked accounts</h2>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
        <UserList
          users={users}
          emptyText="You haven't blocked anyone."
          renderAction={(user) => (
            <button
              type="button"
              onClick={() => handleUnblock(user.id)}
              disabled={busyId === user.id}
              className="rounded-lg bg-neutral-100 px-3 py-1.5 text-xs font-semibold text-neutral-900 transition hover:bg-neutral-200 disabled:opacity-60"
            >
              Unblock
            </button>
          )}
        />
      </div>
    </div>
  );
}
