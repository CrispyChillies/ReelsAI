import styled from "styled-components";
import { useEffect, useState } from "react";
import { useI18n } from "@/app/i18n";
import PwField from "@/components/common/inputs/PwField";
import { useToast } from "@/app/toast";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import LoaderPage from "@/components/common/loaders/LoaderPage";
import dayjs from "dayjs";
import customParseFormat from "dayjs/plugin/customParseFormat";

dayjs.extend(customParseFormat);

type ProfileForm = {
  name: string; // Used as username
  email: string;
};
type PwForm = { current: string; next: string; confirm: string };

/* ===== DateField ===== */

export default function Profile() {
  const { t } = useI18n();
  const { notify } = useToast();
  const { user, isLoadingUser } = useAuth();
  const { updateProfile, isUpdatingProfile, changePassword, isChangingPassword } = useProfile();

  const initial: ProfileForm = {
    name: "",
    email: "",
  };
  const [form, setForm] = useState<ProfileForm>(initial);
  const [backup, setBackup] = useState<ProfileForm>(initial);
  const [editing, setEditing] = useState(false);

  const [pw, setPw] = useState<PwForm>({ current: "", next: "", confirm: "" });
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState<string | null>(null);

  // tự ẩn msg pw sau 4s
  useEffect(() => {
    if (!pwError && !pwSuccess) return;
    const id = setTimeout(() => {
      setPwError(null);
      setPwSuccess(null);
    }, 4000);
    return () => clearTimeout(id);
  }, [pwError, pwSuccess]);

  // Load user profile from useAuth
  useEffect(() => {
    if (user) {
      const profileData: ProfileForm = {
        name: user.username || "",
        email: user.email || "",
      };
      setForm(profileData);
      setBackup(profileData);
    }
  }, [user]);

  if (isLoadingUser) {
    return <LoaderPage />;
  }

  // ========== handlers ==========
  //         dob: p.dob || "",
  //       };
  //       setForm(pf);
  //       setBackup(pf);
  //     } catch (e: any) {
  //       notify({
  //         title: t("error"),
  //         content: e?.response?.data?.detail || e?.message,
  //         tone: "error",
  //       });
  //     }
  //   })();
  // }, [notify, t]);

  const onChange = (k: keyof ProfileForm, v: string) =>
    setForm((prev) => ({ ...prev, [k]: v }));
  const startEdit = () => {
    setBackup(form);
    setEditing(true);
  };
  const cancelEdit = () => {
    setForm(backup);
    setEditing(false);
  };

  const hasDiff = (a: ProfileForm, b: ProfileForm) =>
    a.name !== b.name;

  const save = async () => {
    // ===== Required fields =====
    if (!form.name.trim()) {
      notify({ title: t("error"), content: "Username is required", tone: "error" });
      return;
    }

    if (!hasDiff(form, backup)) {
      notify({ title: t("noChanges"), tone: "info" });
      setEditing(false);
      return;
    }

    // Call API to update profile
    updateProfile(
      {
        username: form.name.trim(),
        email: form.email.trim(),
      },
      {
        onSuccess: () => {
          setBackup(form);
          setEditing(false);
        },
      }
    );
  };

  const onChangePw = async () => {
    setPwError(null);
    setPwSuccess(null);
    if (!pw.current || !pw.next || !pw.confirm) {
      setPwError(t("fillAllPw"));
      return;
    }
    if (pw.next.length < 8) {
      setPwError(t("passwordTooShort"));
      return;
    }
    if (pw.next !== pw.confirm) {
      setPwError(t("passwordNotMatch"));
      return;
    }
    if (pw.current === pw.next) {
      setPwError(t("newPwSameAsCurrent"));
      return;
    }

    // Call API to change password
    changePassword(
      {
        current_password: pw.current,
        new_password: pw.next,
      },
      {
        onSuccess: () => {
          setPwSuccess(t("passwordUpdated"));
          setPw({ current: "", next: "", confirm: "" });
        },
        onError: (error: any) => {
          setPwError(
            error?.response?.data?.error || error?.message || t("passwordUpdateFailed")
          );
        },
      }
    );
  };

  // COMMENTED OUT: Topics feature no longer needed
  // const TOPICS = [
  //   { id: "animals", labelKey: "topicAnimals" },
  //   { id: "anime", labelKey: "topicAnime" },
  //   { id: "art", labelKey: "topicArt" },
  //   { id: "beauty", labelKey: "topicBeauty" },
  //   { id: "books", labelKey: "topicBooks" },
  //   { id: "business", labelKey: "topicBusiness" },
  //   { id: "dance", labelKey: "topicDance" },
  //   { id: "education", labelKey: "topicEducation" },
  //   { id: "entertainment", labelKey: "topicEntertainment" },
  //   { id: "fashion", labelKey: "topicFashion" },
  //   { id: "food", labelKey: "topicFood" },
  //   { id: "gaming", labelKey: "topicGaming" },
  //   { id: "health", labelKey: "topicHealth" },
  //   { id: "lifestyle", labelKey: "topicLifestyle" },
  //   { id: "music", labelKey: "topicMusic" },
  //   { id: "personal", labelKey: "topicPersonal" },
  //   { id: "photography", labelKey: "topicPhotography" },
  //   { id: "sports", labelKey: "topicSports" },
  //   { id: "tech", labelKey: "topicTech" },
  //   { id: "travel", labelKey: "topicTravel" },
  //   { id: "other", labelKey: "topicOther" },
  // ];

  // const toggleTopic = (topicId: string) => {
  //   if (!editingTopics) return;
  //   
  //   setSelectedTopics((prev) => {
  //     if (prev.includes(topicId)) {
  //       // Unselect
  //       return prev.filter((id) => id !== topicId);
  //     } else {
  //       // Select (only if < 5)
  //       if (prev.length >= 5) return prev;
  //       return [...prev, topicId];
  //     }
  //   });
  // };

  // const startEditTopics = () => {
  //   setBackupTopics(selectedTopics);
  //   setEditingTopics(true);
  // };

  // const cancelEditTopics = () => {
  //   setSelectedTopics(backupTopics);
  //   setEditingTopics(false);
  // };

  // const saveTopics = () => {
  //   // Save to localStorage
  //   localStorage.setItem("userTopics", JSON.stringify(selectedTopics));
  //   setBackupTopics(selectedTopics);
  //   setEditingTopics(false);
  //   notify({
  //     title: t("saved"),
  //     content: t("topicsSaved"),
  //     tone: "success",
  //   });
  // };

  return (
    <Wrap>
      {/* ======= Card: Thông tin cá nhân ======= */}
      <div className="card">
        <div className="cardHead">
          <div className="title">
            <h1>{t("profile")}</h1>
            <p className="subtitle">{t("personalInfo")}</p>
          </div>

          <div className="actions">
            {!editing ? (
              <button className="btn accent" onClick={startEdit}>
                {t("edit")}
              </button>
            ) : (
              <>
                <button className="btn ghost" onClick={cancelEdit}>
                  {t("cancel")}
                </button>
                <button 
                  className="btn accent" 
                  onClick={save}
                  disabled={isUpdatingProfile}
                >
                  {isUpdatingProfile ? t("saving") : t("save")}
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid">
          <label>
            <div className="lbl">
              <span>Username</span>
              <span className="req" aria-hidden="true">
                *
              </span>
            </div>
            <input
              aria-required="true"
              disabled={!editing}
              value={form.name}
              onChange={(e) => onChange("name", e.target.value)}
              placeholder="Your username"
            />
          </label>

          <label>
            <div className="lbl">{t("email")}</div>
            <input disabled type="email" value={form.email} readOnly />
          </label>
        </div>
      </div>

      {/* COMMENTED OUT: Topics section no longer needed */}
      {/* <div className="card">
        <div className="cardHead">
          <div className="title">
            <h2>{t("topicsTitle")}</h2>
            <p className="subtitle">
              {t("topicsSubtitle")}
            </p>
          </div>

          <div className="actions">
            {!editingTopics ? (
              <button className="btn accent" onClick={startEditTopics}>
                {t("edit")}
              </button>
            ) : (
              <>
                <button className="btn ghost" onClick={cancelEditTopics}>
                  {t("cancel")}
                </button>
                <button className="btn accent" onClick={saveTopics}>
                  {t("save")}
                </button>
              </>
            )}
          </div>
        </div>

        <div className="topicsGrid">
          {TOPICS.map((topic) => {
            const isSelected = selectedTopics.includes(topic.id);
            const isDisabled = !editingTopics || (!isSelected && selectedTopics.length >= 5);
            
            return (
              <button
                key={topic.id}
                className={`topicBtn ${isSelected ? "selected" : ""} ${isDisabled ? "disabled" : ""}`}
                onClick={() => toggleTopic(topic.id)}
                disabled={isDisabled}
              >
                <TopicIcon id={topic.id} size={28} className="icon" />
                <span className="label">{t(topic.labelKey)}</span>
              </button>
            );
          })}
        </div>

        {editingTopics && (
          <div className="topicHint">
            {t("topicsSelected")} {selectedTopics.length}{t("topicsOf")}5 {t("topicsMax")}
          </div>
        )}
      </div> */}

      {/* ======= Card: Đổi mật khẩu ======= */}
      <div className="card">
        <div className="cardHead">
          <div className="title">
            <h2>{t("changePassword")}</h2>
            <p className="subtitle">{t("changePasswordSubtitle")}</p>
          </div>
        </div>

        <div className="grid pwGrid">
          <PwField
            label={t("currentPassword")}
            value={pw.current}
            onChange={(v) => setPw((p) => ({ ...p, current: v }))}
            autoComplete="current-password"
          />
          <PwField
            label={t("newPassword")}
            value={pw.next}
            onChange={(v) => setPw((p) => ({ ...p, next: v }))}
            autoComplete="new-password"
          />
          <PwField
            label={t("confirmNewPassword")}
            value={pw.confirm}
            onChange={(v) => setPw((p) => ({ ...p, confirm: v }))}
            autoComplete="new-password"
          />
        </div>

        <div className="pwActions">
          {pwError && <div className="msg error">{pwError}</div>}
          {pwSuccess && <div className="msg success">{pwSuccess}</div>}
          <button
            className="btn accent"
            onClick={onChangePw}
            disabled={isChangingPassword}
          >
            {isChangingPassword ? t("updating") : t("updatePassword")}
          </button>
        </div>
      </div>
    </Wrap>
  );
}

/* ===================== styles ===================== */
const Wrap = styled.div`
  position: relative;
  min-height: 100vh;
  background: #ffffff;
  padding: 20px;
  
  /* Grid lines - full viewport width but start from sidebar edge */
  &::before {
    content: '';
    position: fixed;
    top: 0;
    bottom: 0;
    left: 280px; /* sidebar width */
    right: 0;
    z-index: 0;
    background-image: 
      linear-gradient(to right, rgba(13, 148, 136, 0.15) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(13, 148, 136, 0.15) 1px, transparent 1px);
    background-size: 40px 40px;
    mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    pointer-events: none;
  }
  
  /* Subtle teal glow at top */
  &::after {
    content: '';
    position: fixed;
    top: 0;
    left: 280px; /* sidebar width */
    right: 0;
    height: 200px;
    background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(13, 148, 136, 0.03), transparent 70%);
    pointer-events: none;
    z-index: 0;
  }
  
  /* Content wrapper with max-width */
  > * {
    position: relative;
    z-index: 1;
    max-width: 920px;
    margin: 0 auto;
  }
  
  /* Responsive: adjust for collapsed sidebar */
  @media (max-width: 1280px) {
    &::before,
    &::after {
      left: 68px; /* collapsed sidebar width */
    }
  }
  
  /* Responsive: mobile - full width grid */
  @media (max-width: 980px) {
    &::before,
    &::after {
      left: 0;
    }
  }

  .card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(13, 148, 136, 0.15);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(13, 148, 136, 0.08);
    transition: all 0.3s ease;
    + .card { margin-top: 20px; }
  }
  
  .card:hover {
    box-shadow: 0 6px 24px rgba(13, 148, 136, 0.12);
    transform: translateY(-2px);
  }

  .cardHead {
    display: flex; 
    align-items: center; 
    gap: 12px; 
    justify-content: space-between;
    border-bottom: 2px solid rgba(13, 148, 136, 0.1);
    padding-bottom: 16px; 
    margin-bottom: 20px;
  }

  h1, h2 { 
    margin: 0; 
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.accent2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .subtitle { 
    margin: 6px 0 0; 
    color: ${({ theme }) => theme.colors.secondary}; 
    font-size: .92rem;
    font-weight: 500;
  }

  .actions { display: inline-flex; gap: 10px; }

  .btn {
    height: 38px; 
    padding: 0 18px; 
    border-radius: 10px; 
    border: none; 
    font-size: 0.92rem;
    font-weight: 600; 
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .btn.ghost { 
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(13, 148, 136, 0.2);
    color: ${({ theme }) => theme.colors.accent2};
  }
  .btn.ghost:hover { 
    background: rgba(255, 255, 255, 1);
    border-color: ${({ theme }) => theme.colors.accent};
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.15);
  }
  
  .btn.accent { 
    background: linear-gradient(90deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.accent2} 100%);
    color: #fff;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
  }
  .btn.accent:hover { 
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(13, 148, 136, 0.35);
  }
  .btn.accent:active { transform: translateY(0); }
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(240px,1fr)); gap:16px; }
  .pwGrid { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }

  label { display:flex; flex-direction:column; gap:8px; }
  .lbl { 
    display:flex; 
    align-items:center; 
    gap:4px; 
    line-height:1;
    font-size: 0.9rem;
    font-weight: 600;
    color: ${({ theme }) => theme.colors.accent2};
  }
  .req { color: #ef4444; font-size: 1.1rem; }

  input {
    height: 42px; 
    padding: 0 14px; 
    border-radius: 10px; 
    border: 1.5px solid rgba(13, 148, 136, 0.2);
    outline: none; 
    background: #ffffff;
    color: ${({ theme }) => theme.colors.primary};
    font-size: 0.95rem;
    transition: all 0.2s ease;
  }
  input:focus { 
    border-color: ${({ theme }) => theme.colors.accent};
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15);
    transform: translateY(-1px);
  }
  input:disabled { 
    background: rgba(249, 250, 251, 0.8);
    color: ${({ theme }) => theme.colors.secondary};
    cursor: not-allowed;
    border-color: rgba(13, 148, 136, 0.1);
  }

  /* DateField */
  .dateField { position: relative; display:flex; align-items:center; }
  .dateField input[aria-invalid="true"] { 
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
  }
  .dateField .native { position:absolute; inset:0; opacity:0; pointer-events:none; }
  .dateField .calendarBtn { 
    position:absolute; 
    right:8px; 
    top:50%; 
    transform:translateY(-50%); 
    width:32px; 
    height:32px; 
    border:none; 
    border-radius:8px; 
    background:transparent; 
    color:${({ theme }) => theme.colors.accent}; 
    display:grid; 
    place-items:center; 
    cursor:pointer;
    transition: all 0.2s ease;
  }
  .dateField .calendarBtn:hover { 
    background: rgba(13, 148, 136, 0.1);
    transform: translateY(-50%) scale(1.1);
  }

  .pwActions { 
    display:flex; 
    align-items:center; 
    gap:12px; 
    margin-top:16px; 
    justify-content:flex-end;
    flex-wrap: wrap;
  }
  .msg { 
    padding:8px 14px; 
    border-radius:10px; 
    font-weight:600;
    font-size: 0.9rem;
    flex: 1;
    min-width: 200px;
  }
  .msg.small { font-size:.85rem; padding:6px 10px; }
  .msg.error { 
    background: rgba(239, 68, 68, 0.1);
    color: #dc2626;
    border: 1px solid rgba(239, 68, 68, 0.2);
  }
  .msg.success { 
    background: rgba(13, 148, 136, 0.1);
    color: #0d9488;
    border: 1px solid rgba(13, 148, 136, 0.2);
  }

  /* Topics Section */
  .topicsGrid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-top: 4px;
  }

  .topicBtn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 12px;
    border: 2px solid rgba(13, 148, 136, 0.2);
    background: #ffffff;
    color: ${({ theme }) => theme.colors.primary};
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }

  .topicBtn:hover:not(.disabled) {
    border-color: ${({ theme }) => theme.colors.accent};
    background: rgba(13, 148, 136, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15);
  }

  .topicBtn.selected {
    background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.accent2} 100%);
    border-color: ${({ theme }) => theme.colors.accent};
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
  }

  .topicBtn.selected:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
  }

  .topicBtn.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    border-color: rgba(13, 148, 136, 0.1);
  }

  .topicBtn.disabled:not(.selected) {
    background: rgba(249, 250, 251, 0.8);
  }

  .topicBtn .icon {
    color: ${({ theme }) => theme.colors.accent2};
    flex-shrink: 0;
    transition: all 0.3s ease;
  }

  .topicBtn.selected .icon {
    color: white;
    transform: scale(1.1);
  }

  .topicBtn .label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .topicHint {
    margin-top: 16px;
    padding: 10px 14px;
    border-radius: 10px;
    background: rgba(13, 148, 136, 0.1);
    color: ${({ theme }) => theme.colors.accent2};
    font-weight: 600;
    font-size: 0.9rem;
    text-align: center;
    border: 1px solid rgba(13, 148, 136, 0.2);
  }
`;
