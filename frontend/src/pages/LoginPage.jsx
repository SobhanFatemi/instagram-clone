import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const RESEND_SECONDS = 60;

function extractError(error) {
  const data = error?.response?.data;
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

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [step, setStep] = useState("request");
  const [channel, setChannel] = useState("email");
  const [target, setTarget] = useState("");
  const [code, setCode] = useState("");
  const [purpose, setPurpose] = useState(null);
  const [devCode, setDevCode] = useState(null);
  const [resendIn, setResendIn] = useState(0);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (!loading && user) {
      navigate(redirectTo, { replace: true });
    }
  }, [loading, user, navigate, redirectTo]);

  useEffect(() => {
    if (resendIn <= 0) return undefined;
    const timer = setInterval(() => {
      setResendIn((value) => (value > 0 ? value - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendIn]);

  function switchChannel(next) {
    setChannel(next);
    setTarget("");
    setError("");
  }

  async function requestOtp(event) {
    if (event) event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post("/auth/otp/request/", {
        channel,
        target_value: target.trim(),
      });
      setPurpose(data.purpose || null);
      setDevCode(data.dev_code || null);
      setCode("");
      setResendIn(RESEND_SECONDS);
      setStep("verify");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function verifyOtp(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post("/auth/otp/verify/", {
        channel,
        target_value: target.trim(),
        code: code.trim(),
      });
      await login(data.tokens);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(extractError(err));
    } finally {
      setSubmitting(false);
    }
  }

  function backToRequest() {
    setStep("request");
    setCode("");
    setError("");
    setDevCode(null);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm space-y-4">
        <div className="rounded-xl border border-neutral-200 bg-white px-8 py-10">
          <h1 className="mb-8 text-center text-3xl font-semibold tracking-tight">
            Instagram
          </h1>

          {step === "request" ? (
            <form onSubmit={requestOtp} className="space-y-4">
              <div className="grid grid-cols-2 rounded-lg bg-neutral-100 p-1 text-sm">
                <button
                  type="button"
                  onClick={() => switchChannel("email")}
                  className={`rounded-md py-2 font-medium transition ${
                    channel === "email"
                      ? "bg-white shadow-sm"
                      : "text-neutral-500"
                  }`}
                >
                  Email
                </button>
                <button
                  type="button"
                  onClick={() => switchChannel("phone")}
                  className={`rounded-md py-2 font-medium transition ${
                    channel === "phone"
                      ? "bg-white shadow-sm"
                      : "text-neutral-500"
                  }`}
                >
                  Phone
                </button>
              </div>

              <input
                type={channel === "email" ? "email" : "tel"}
                value={target}
                onChange={(event) => setTarget(event.target.value)}
                placeholder={
                  channel === "email" ? "you@example.com" : "09123456789"
                }
                autoComplete={channel === "email" ? "email" : "tel"}
                className="w-full rounded-lg border border-neutral-300 bg-neutral-50 px-3 py-2.5 text-sm outline-none focus:border-neutral-500"
                required
              />

              {error && <p className="text-sm text-red-600">{error}</p>}

              <button
                type="submit"
                disabled={submitting || !target.trim()}
                className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
              >
                {submitting ? "Sending..." : "Send code"}
              </button>

              <p className="text-center text-xs text-neutral-400">
                We'll create an account automatically if you're new.
              </p>
            </form>
          ) : (
            <form onSubmit={verifyOtp} className="space-y-4">
              <p className="text-center text-sm text-neutral-600">
                Enter the 6-digit code sent to
                <br />
                <span className="font-medium text-neutral-900">{target}</span>
                {purpose === "signup" && (
                  <span className="mt-1 block text-xs text-sky-600">
                    Creating a new account
                  </span>
                )}
              </p>

              {devCode && (
                <div className="flex items-center justify-between rounded-lg border border-dashed border-amber-300 bg-amber-50 px-3 py-2 text-sm">
                  <span className="text-amber-700">
                    Dev code: <strong>{devCode}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={() => setCode(devCode)}
                    className="text-xs font-semibold text-amber-700 underline"
                  >
                    Autofill
                  </button>
                </div>
              )}

              <input
                inputMode="numeric"
                value={code}
                onChange={(event) =>
                  setCode(event.target.value.replace(/\D/g, "").slice(0, 6))
                }
                placeholder="••••••"
                className="w-full rounded-lg border border-neutral-300 bg-neutral-50 px-3 py-2.5 text-center text-lg tracking-[0.5em] outline-none focus:border-neutral-500"
                required
              />

              {error && <p className="text-sm text-red-600">{error}</p>}

              <button
                type="submit"
                disabled={submitting || code.length !== 6}
                className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
              >
                {submitting ? "Verifying..." : "Verify & continue"}
              </button>

              <div className="flex items-center justify-between text-xs text-neutral-500">
                <button
                  type="button"
                  onClick={backToRequest}
                  className="hover:text-neutral-800"
                >
                  Change {channel === "email" ? "email" : "phone"}
                </button>
                <button
                  type="button"
                  onClick={() => requestOtp()}
                  disabled={resendIn > 0 || submitting}
                  className="hover:text-neutral-800 disabled:opacity-50"
                >
                  {resendIn > 0 ? `Resend in ${resendIn}s` : "Resend code"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
