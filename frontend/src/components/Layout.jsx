import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { getConversations } from "../api/messaging";
import { getUnreadCount } from "../api/notifications";
import { useAuth } from "../auth/AuthContext";

const BADGE_POLL_INTERVAL = 20000;

const navItems = [
  { to: "/", label: "Home", end: true, icon: HomeIcon },
  { to: "/search", label: "Search", icon: SearchIcon },
  { to: "/explore", label: "Explore", icon: ExploreIcon },
  { to: "/messages", label: "Messages", icon: MessageIcon },
  { to: "/notifications", label: "Notifications", icon: HeartIcon },
  { to: "/create", label: "Create", icon: CreateIcon },
  { to: "/profile", label: "Profile", icon: ProfileIcon },
];

const mobileBottomItems = [
  { to: "/", label: "Home", end: true, icon: HomeIcon },
  { to: "/search", label: "Search", icon: SearchIcon },
  { to: "/explore", label: "Explore", icon: ExploreIcon },
  { to: "/create", label: "Create", icon: CreateIcon },
  { to: "/profile", label: "Profile", icon: ProfileIcon },
];

const mobileTopItems = [
  { to: "/notifications", label: "Notifications", icon: HeartIcon },
  { to: "/messages", label: "Messages", icon: MessageIcon },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messageBadge, setMessageBadge] = useState(0);
  const [notificationBadge, setNotificationBadge] = useState(0);

  useEffect(() => {
    let active = true;

    async function poll() {
      try {
        const conversations = await getConversations();
        if (active) {
          setMessageBadge(
            conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0)
          );
        }
      } catch {
        /* ignore */
      }
      try {
        const { unread_count } = await getUnreadCount();
        if (active) setNotificationBadge(unread_count || 0);
      } catch {
        /* ignore */
      }
    }

    poll();
    const timer = setInterval(poll, BADGE_POLL_INTERVAL);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const badges = {
    "/messages": messageBadge,
    "/notifications": notificationBadge,
  };

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen bg-neutral-50">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-neutral-200 bg-white px-4 py-6 md:flex">
        <h1 className="px-3 pb-8 text-2xl font-semibold tracking-tight">
          Instagram
        </h1>

        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map(({ to, label, end, icon: Icon }) => {
            const badge = badges[to] || 0;
            return (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex items-center gap-4 rounded-lg px-3 py-3 text-[15px] transition hover:bg-neutral-100 ${
                    isActive ? "font-semibold" : "font-normal"
                  }`
                }
              >
                <span className="relative">
                  <Icon />
                  {badge > 0 && (
                    <span className="absolute -right-2 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-sky-500 px-1 text-[10px] font-semibold text-white">
                      {badge > 99 ? "99+" : badge}
                    </span>
                  )}
                </span>
                <span>{label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-4 border-t border-neutral-200 pt-4">
          <div className="px-3 pb-3 text-sm">
            <p className="font-medium text-neutral-900">
              {user?.username || "user"}
            </p>
            <p className="truncate text-neutral-400">
              {user?.email || user?.phone_number || ""}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full rounded-lg px-3 py-2 text-left text-[15px] text-red-600 transition hover:bg-red-50"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-neutral-200 bg-white px-4 py-2.5 md:hidden">
          <h1 className="text-xl font-semibold">Instagram</h1>
          <div className="flex items-center gap-0.5">
            {mobileTopItems.map(({ to, label, icon: Icon }) => {
              const badge = badges[to] || 0;
              return (
                <NavLink
                  key={to}
                  to={to}
                  aria-label={label}
                  className={({ isActive }) =>
                    `relative rounded-full p-2 transition hover:bg-neutral-100 ${
                      isActive ? "text-neutral-900" : "text-neutral-600"
                    }`
                  }
                >
                  <Icon />
                  {badge > 0 && (
                    <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-sky-500 px-1 text-[10px] font-semibold text-white">
                      {badge > 99 ? "99+" : badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
            <button
              type="button"
              onClick={handleLogout}
              className="ml-1 text-sm font-medium text-red-600"
            >
              Log out
            </button>
          </div>
        </header>

        {user?.is_generated_username && (
          <div className="border-b border-amber-200 bg-amber-50 px-4 py-2.5">
            <p className="mx-auto flex max-w-2xl flex-wrap items-center gap-x-2 gap-y-1 text-sm text-amber-800">
              <span>
                You're still using an auto-generated username
                {user.username ? ` (${user.username})` : ""}.
              </span>
              <NavLink
                to="/accounts/edit"
                className="font-semibold underline transition hover:text-amber-900"
              >
                Choose your own &rarr;
              </NavLink>
            </p>
          </div>
        )}

        <div className="mx-auto w-full max-w-2xl px-4 py-6 pb-24 md:pb-6">
          <Outlet />
        </div>
      </main>

      <nav className="fixed bottom-0 left-0 right-0 z-20 flex items-center justify-around border-t border-neutral-200 bg-white px-2 py-1.5 md:hidden">
        {mobileBottomItems.map(({ to, label, end, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            aria-label={label}
            className={({ isActive }) =>
              `flex items-center justify-center rounded-lg px-4 py-2 transition ${
                isActive ? "text-neutral-900" : "text-neutral-500"
              }`
            }
          >
            <Icon />
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

function HomeIcon() {
  return (
    <Icon>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
    </Icon>
  );
}

function SearchIcon() {
  return (
    <Icon>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </Icon>
  );
}

function ExploreIcon() {
  return (
    <Icon>
      <circle cx="12" cy="12" r="9" />
      <path d="m15 9-2 4-4 2 2-4 4-2Z" />
    </Icon>
  );
}

function MessageIcon() {
  return (
    <Icon>
      <path d="M21 11.5a8 8 0 0 1-11.5 7.2L4 20l1.3-4.5A8 8 0 1 1 21 11.5Z" />
    </Icon>
  );
}

function HeartIcon() {
  return (
    <Icon>
      <path d="M12 20s-7-4.6-9.3-9A4.7 4.7 0 0 1 12 6a4.7 4.7 0 0 1 9.3 5c-2.3 4.4-9.3 9-9.3 9Z" />
    </Icon>
  );
}

function CreateIcon() {
  return (
    <Icon>
      <rect x="3" y="3" width="18" height="18" rx="4" />
      <path d="M12 8v8M8 12h8" />
    </Icon>
  );
}

function ProfileIcon() {
  return (
    <Icon>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </Icon>
  );
}

function Icon({ children }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  );
}
