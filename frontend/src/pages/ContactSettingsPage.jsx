import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  getMe,
  requestContactOtp,
  verifyContactOtp,
} from "../api/accounts";
import { useAuth } from "../auth/AuthContext";
import Spinner from "../components/Spinner";

export default function ContactSettingsPage() {
  const { refreshUser } = useAuth();
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setMe(await getMe());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleUpdated(updated) {
    setMe(updated);
    refreshUser();
  }

  if (loading) return <Spinner label="Loading..." />;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/accounts/edit"
          className="text-sm text-neutral-500 transition hover:text-neutral-800"
        >
          &larr; Back
        </Link>
        <h2 className="text-xl font-semibold text-neutral-900">Email & phone</h2>
      </div>

      <ContactCard
        channel="email"
        label="Email"
        current={me.email}
        suggestion="Add an email address so you can also log in and recover your account with it."
        onUpdated={handleUpdated}
      />

      <ContactCard
        channel="phone"
        label="Phone number"
        current={me.phone_number}
        suggestion="Add a phone number so you can also log in with it."
        onUpdated={handleUpdated}
      />
    </div>
  );
}

function ContactCard({ channel, label, current, suggestion, onUpdated }) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState("input");
  const [value, setValue] = useState("");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const timer = useRef(null);

  useEffect(() => {
    return () => clearInterval(timer.current);
  }, []);

  function startCooldown() {
    setCooldown(60);
    clearInterval(timer.current);
    timer.current = setInterval(() => {
      setCooldown((c) => {
        if (c <= 1) {
          clearInterval(timer.current);
          return 0;
        }
        return c - 1;
      });
    }, 1000);
  }

  function reset() {
    setOpen(false);
    setStep("input");
    setValue("");
    setCode("");
    setDevCode(null);
    setError("");
    setCooldown(0);
    clearInterval(timer.current);
  }

  async function sendCode(event) {
    if (event) event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const data = await requestContactOtp({ channel, target_value: value });
      setDevCode(data.dev_code || null);
      setCode(data.dev_code || "");
      setStep("code");
      startCooldown();
    } catch (err) {
      setError(extractError(err));
    } finally {
      setBusy(false);
    }
  }

  async function verify(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const updated = await verifyContactOtp({
        channel,
        target_value: value,
        code,
      });
      onUpdated(updated);
      reset();
    } catch (err) {
      setError(extractError(err));
    } finally {
      setBusy(false);
    }
  }

  const inputType = channel === "email" ? "email" : "tel";
  const placeholder = channel === "email" ? "you@example.com" : "09xxxxxxxxx";

  return (
    <div className="space-y-4 rounded-xl border border-neutral-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-neutral-900">{label}</p>
          {current ? (
            <p className="truncate text-sm text-neutral-600">{current}</p>
          ) : (
            <p className="text-sm text-amber-600">Not added yet</p>
          )}
        </div>
        {!open && (
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="shrink-0 rounded-lg bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200"
          >
            {current ? "Change" : "Add"}
          </button>
        )}
      </div>

      {!open && !current && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          {suggestion}
        </p>
      )}

      {open && (
        <div className="space-y-3 border-t border-neutral-100 pt-4">
          {step === "input" ? (
            <form onSubmit={sendCode} className="space-y-3">
              <input
                type={inputType}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={placeholder}
                autoFocus
                className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={busy || !value.trim()}
                  className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
                >
                  {busy ? "Sending..." : "Send code"}
                </button>
                <button
                  type="button"
                  onClick={reset}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-neutral-600 transition hover:bg-neutral-100"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={verify} className="space-y-3">
              <p className="text-sm text-neutral-600">
                Enter the code sent to{" "}
                <span className="font-semibold text-neutral-900">{value}</span>.{" "}
                <button
                  type="button"
                  onClick={() => setStep("input")}
                  className="text-sky-500 hover:underline"
                >
                  Change
                </button>
              </p>

              {devCode && (
                <p className="rounded-lg bg-neutral-100 px-3 py-2 text-xs text-neutral-600">
                  Dev code: <span className="font-semibold">{devCode}</span>
                </p>
              )}

              <input
                type="text"
                inputMode="numeric"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="6-digit code"
                maxLength={6}
                className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm tracking-widest outline-none focus:border-neutral-500"
              />

              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={busy || !code.trim()}
                  className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
                >
                  {busy ? "Verifying..." : "Verify"}
                </button>
                <button
                  type="button"
                  onClick={() => sendCode()}
                  disabled={busy || cooldown > 0}
                  className="text-sm font-medium text-neutral-500 transition hover:text-neutral-700 disabled:opacity-50"
                >
                  {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
                </button>
              </div>
            </form>
          )}

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function extractError(err) {
  const data = err.response?.data;
  if (!data) return "Something went wrong. Please try again.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    return Array.isArray(value) ? value[0] : String(value);
  }
  return "Something went wrong. Please try again.";
}
