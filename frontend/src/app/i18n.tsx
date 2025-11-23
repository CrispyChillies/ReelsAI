import React, { createContext, useContext, useMemo, useState, useEffect } from "react";

type Lang = "en" | "vi";
type Dict = Record<string, string>;

const DICTS: Record<Lang, Dict> = {
  en: {
    appTitle: "ReelsAI",

    // Auth & shared
    signin: "Sign In",
    signup: "Sign Up",
    email: "Email",
    password: "Password",
    confirmPassword: "Confirm Password",
    fullName: "Full name",
    login: "Login",
    createAccount: "Create account",
    forgot: "Forgot password",
    haveAccount: "Already have an account?",
    needAccount: "Don’t have an account?",
    sending: "Sending...",
    loggingIn: "Logging in...",
    creating: "Creating...",
    logout: "Logout",

    // Chat & sidebar
    feed: "Feed",
    saved: "Saved",
    contentStorage: "Content Storage",
    home: "Home",
    aiChat: "AI Chat",
    history: "History",
    heroTitle: "What do you want to see?",
    you_asked: "You asked:",
    noSessions: "No sessions yet",
    settings: "Settings",
    language: "Language",
    signedOut: "Signed out.",
    send: "Send",
    newChat: "New chat",
    searchChats: "Search chats",
    chats: "Chats",
    more: "More",
    rename: "Rename",
    delete: "Delete",
    confirmDelete: "Delete this session?",
    deleteWarning: "Are you sure you want to delete? This action cannot be undone!",
    search: "Search",

    // App
    addLink: "Add website link",
    enterPrompt: "Type your request...",
    linkPlaceholder: "Paste website link (e.g. https://dichvucong.gov.vn)",
    urlInPromptWarn:
      "You pasted a URL into the Prompt. Please put it into + link box instead.",

    // Reset (request email)
    resetTitle: "Reset password",
    resetBtn: "Send reset link",
    resetSent: "Password reset email sent (if the email exists).",

    // Reset flow (set new password page)
    setNewPassword: "Set a new password",
    newPassword: "New password",
    updatePassword: "Update password",
    passwordUpdated: "Password updated successfully.",
    passwordTooShort: "Password must be at least 8 characters.",

    // Profile
    profile: "Profile",
    personalInfo: "Your personal information",
    edit: "Edit",
    save: "Save",
    cancel: "Cancel",
    age: "Age",
    city: "City / District",
    phone: "Phone",
    dob: "Date of birth",
    changePassword: "Change password",
    changePasswordSubtitle: "Update your password for this account",
    currentPassword: "Current password",
    confirmNewPassword: "Confirm new password",
    updating: "Updating...",
    passwordNotMatch: "New password confirmation does not match.",
    passwordUpdateFailed: "Failed to update password.",

    // Used by Profile validations / toasts
    requireName: "Please enter your full name.",
    requireAge: "Please enter your age.",
    requireCity: "Please enter your city/district.",
    ageInteger: "Age must be an integer.",
    ageRange: `Age must be between ${14}–${100}.`,
    dobInvalid: "Invalid date of birth.",
    dobFuture: "Date of birth cannot be in the future.",
    ageDobMismatch: "Age does not match date of birth.",
    noChanges: "No changes to save.",
    savedSuccess: "Saved.",

    // DateField
    invalidDateLead: "Please enter a valid date in",
    pickDate: "Pick a date",

    // Password helpers
    fillAllPw: "Please fill in all password fields.",
    newPwSameAsCurrent: "New password must be different from the current password.",

    // Topics
    topicsTitle: "Choose your category",
    topicsSubtitle: "Based on your categories, we will show you related topics",
    topicsSaved: "Your favorite topics have been saved",
    topicsSelected: "Selected",
    topicsOf: "/",
    topicsMax: "topics",
    // Topic names
    topicAnimals: "Animals",
    topicAnime: "Anime",
    topicArt: "Art",
    topicBeauty: "Beauty",
    topicBooks: "Books & Writing",
    topicBusiness: "Business",
    topicDance: "Dance",
    topicEducation: "Education",
    topicEntertainment: "Entertainment",
    topicFashion: "Fashion",
    topicFood: "Food",
    topicGaming: "Gaming",
    topicHealth: "Health",
    topicLifestyle: "Lifestyle",
    topicMusic: "Music",
    topicPersonal: "Personal",
    topicPhotography: "Photography",
    topicSports: "Sports",
    topicTech: "Technology",
    topicTravel: "Travel",
    topicOther: "Other",

    // Onboarding
    onboardingTitle: "What are you interested in?",
    onboardingSubtitle: "Choose topics you'd like to see, and we'll recommend content just for you",
    onboardingSkip: "Skip",
    onboardingContinue: "Continue",
    onboardingSelectMin: "Please select at least one topic to continue",
    onboardingSuccess: "Great! Your preferences have been saved",

    // Toast / statuses
    signupVerify: "Sign-up success. Verification email sent.",
    signinSuccess: "Sign-in success.",
    error: "Error",

    // Disclaimer
    chatDisclaimer: "ChatGOV can make mistakes. Check important info.",

    // Content Storage
    contentStorageTitle: "Content Storage",
    contentStorageSubtitle: "AI-powered content saved for knowledge graph",
    savedItems: "items",
    noSavedContent: "No saved content yet",
    noSavedDesc: "Save posts from your newsfeed to build your knowledge graph",
    platform: "Platform",
    author: "Author",
    content: "Content",
    engagement: "Engagement",
    savedTime: "Saved",
    actions: "Actions",
    remove: "Remove",
    hasMedia: "Has media",
    viewPost: "View post",
    confirmRemoveTitle: "Remove saved item?",
    confirmRemoveMessage: "Are you sure you want to remove this item from your saved content? This action cannot be undone.",
    confirmRemoveBtn: "Remove",

    checkInbox: "Check your inbox",
    verifySentDesc: "We sent a verification email to",
    resetSentDesc: "We sent a password reset link to",
    openMailbox: "Open Email Inbox",
    backToSignin: "Back to sign in?",
    noEmail: "Didn't receive the email?",
    checkSpam: "Check your Spam/Junk folder",
    waitMinute: "Please wait 1-3 minutes and check again",
  },

  vi: {
    appTitle: "ReelsAI",

    // Auth & shared
    signin: "Đăng nhập",
    signup: "Đăng ký",
    email: "Email",
    password: "Mật khẩu",
    confirmPassword: "Xác nhận mật khẩu",
    fullName: "Họ và tên",
    login: "Đăng nhập",
    createAccount: "Tạo tài khoản",
    forgot: "Quên mật khẩu",
    haveAccount: "Đã có tài khoản?",
    needAccount: "Chưa có tài khoản?",
    sending: "Đang gửi...",
    loggingIn: "Đang đăng nhập...",
    creating: "Đang tạo...",
    logout: "Đăng xuất",

    // Chat & sidebar
    feed: "Bảng tin",
    saved: "Đã lưu",
    contentStorage: "Kho nội dung",
    home: "Trang chủ",
    aiChat: "Chat AI",
    history: "Lịch sử",
    heroTitle: "Bạn đang muốn xem gì?",
    you_asked: "Bạn vừa hỏi:",
    noSessions: "Chưa có phiên nào",
    settings: "Cài đặt",
    language: "Ngôn ngữ",
    signedOut: "Đã đăng xuất.",
    send: "Gửi",
    newChat: "Đoạn chat mới",
    searchChats: "Tìm kiếm đoạn chat",
    chats: "Các phiên Chat",
    more: "Thêm tuỳ chọn",
    rename: "Đổi tên",
    delete: "Xoá",
    confirmDelete: "Xóa phiên này?",
    deleteWarning: "Bạn xác nhận xóa? Hành động này không thể hoàn tác!",
    search: "Tìm kiếm",

    // App
    addLink: "Thêm link website",
    enterPrompt: "Nhập yêu cầu của bạn...",
    linkPlaceholder: "Dán link website (vd: https://dichvucong.gov.vn)",
    urlInPromptWarn: "Bạn dán URL trong Prompt. Hãy nhập link vào ô dấu +.",

    // Reset (request email)
    resetTitle: "Quên mật khẩu",
    resetBtn: "Gửi link đặt lại",
    resetSent: "Đã gửi email đặt lại mật khẩu (nếu email tồn tại).",

    // Reset flow (set new password page)
    setNewPassword: "Đặt mật khẩu mới",
    newPassword: "Mật khẩu mới",
    updatePassword: "Cập nhật mật khẩu",
    passwordUpdated: "Đổi mật khẩu thành công.",
    passwordTooShort: "Mật khẩu phải có tối thiểu 8 ký tự.",

    // Profile
    profile: "Hồ sơ",
    personalInfo: "Thông tin cá nhân của bạn",
    edit: "Chỉnh sửa",
    save: "Lưu",
    cancel: "Huỷ",
    age: "Tuổi",
    city: "Nơi sống (Quận/Huyện)",
    phone: "Số điện thoại",
    dob: "Ngày sinh",
    changePassword: "Đổi mật khẩu",
    changePasswordSubtitle: "Cập nhật mật khẩu cho tài khoản của bạn",
    currentPassword: "Mật khẩu hiện tại",
    confirmNewPassword: "Xác nhận mật khẩu mới",
    updating: "Đang cập nhật...",
    passwordNotMatch: "Xác nhận mật khẩu mới không khớp.",
    passwordUpdateFailed: "Cập nhật mật khẩu không thành công.",

    // Used by Profile validations / toasts
    requireName: "Vui lòng nhập Họ và tên.",
    requireAge: "Vui lòng nhập Tuổi.",
    requireCity: "Vui lòng nhập Nơi sống (Quận/Huyện).",
    ageInteger: "Tuổi phải là số nguyên.",
    ageRange: `Độ tuổi phải từ ${14}–${100}.`,
    dobInvalid: "Ngày sinh không hợp lệ.",
    dobFuture: "Ngày sinh không được lớn hơn hiện tại.",
    ageDobMismatch: "Tuổi không khớp với ngày sinh.",
    noChanges: "Không có thay đổi nào.",
    savedSuccess: "Đã lưu.",

    // DateField
    invalidDateLead: "Vui lòng nhập ngày theo định dạng",
    pickDate: "Chọn ngày",

    // Password helpers
    fillAllPw: "Vui lòng điền đầy đủ các ô mật khẩu.",
    newPwSameAsCurrent: "Mật khẩu mới phải khác mật khẩu hiện tại.",

    // Topics
    topicsTitle: "Chọn thể loại của bạn",
    topicsSubtitle: "Dựa trên danh mục của bạn, chúng tôi sẽ hiển thị cho bạn các chủ đề liên quan",
    topicsSaved: "Đã lưu chủ đề yêu thích của bạn",
    topicsSelected: "Đã chọn",
    topicsOf: "/",
    topicsMax: "chủ đề",
    // Topic names
    topicAnimals: "Động vật",
    topicAnime: "Anime",
    topicArt: "Nghệ thuật",
    topicBeauty: "Vẻ đẹp",
    topicBooks: "Sách & Viết",
    topicBusiness: "Kinh doanh",
    topicDance: "Khiêu vũ",
    topicEducation: "Giáo dục",
    topicEntertainment: "Giải trí",
    topicFashion: "Thời trang",
    topicFood: "Thức ăn",
    topicGaming: "Trò chơi",
    topicHealth: "Sức khỏe",
    topicLifestyle: "Phong cách sống",
    topicMusic: "Âm nhạc",
    topicPersonal: "Cá nhân",
    topicPhotography: "Nhiếp ảnh",
    topicSports: "Thể thao",
    topicTech: "Công nghệ",
    topicTravel: "Du lịch",
    topicOther: "Khác",

    // Onboarding
    onboardingTitle: "Bạn quan tâm đến điều gì?",
    onboardingSubtitle: "Chọn chủ đề bạn muốn xem, và chúng tôi sẽ đề xuất nội dung phù hợp với bạn",
    onboardingSkip: "Bỏ qua",
    onboardingContinue: "Tiếp tục",
    onboardingSelectMin: "Vui lòng chọn ít nhất một chủ đề để tiếp tục",
    onboardingSuccess: "Tuyệt vời! Sở thích của bạn đã được lưu",

    // Toast / statuses
    signupVerify: "Đăng ký thành công. Đã gửi email xác nhận.",
    signinSuccess: "Đăng nhập thành công.",
    error: "Lỗi",

    // Disclaimer
    chatDisclaimer: "ChatGOV có thể sai sót. Hãy kiểm tra thông tin quan trọng.",

    // Content Storage
    contentStorageTitle: "Kho nội dung",
    contentStorageSubtitle: "Nội dung được lưu cho đồ thị tri thức AI",
    savedItems: "mục",
    noSavedContent: "Chưa có nội dung đã lưu",
    noSavedDesc: "Lưu các bài đăng từ bảng tin để xây dựng đồ thị tri thức",
    platform: "Nền tảng",
    author: "Tác giả",
    content: "Nội dung",
    engagement: "Tương tác",
    savedTime: "Đã lưu",
    actions: "Hành động",
    remove: "Xóa",
    hasMedia: "Có phương tiện",
    viewPost: "Xem bài viết",
    confirmRemoveTitle: "Xóa mục đã lưu?",
    confirmRemoveMessage: "Bạn có chắc muốn xóa mục này khỏi nội dung đã lưu? Hành động này không thể hoàn tác.",
    confirmRemoveBtn: "Xóa",

    checkInbox: "Hãy kiểm tra hộp thư",
    verifySentDesc: "Chúng tôi đã gửi email xác minh tới",
    resetSentDesc: "Chúng tôi đã gửi liên kết đặt lại mật khẩu tới",
    openMailbox: "Mở hộp thư Email",
    backToSignin: "Quay lại đăng nhập?",
    noEmail: "Không thấy email?",
    checkSpam: "Kiểm tra thư mục Spam/Rác",
    waitMinute: "Vui lòng chờ 1–3 phút rồi check lại",
  },
};

type I18nCtx = { lang: Lang; t: (k: string) => string; setLang: (l: Lang) => void; };
const Ctx = createContext<I18nCtx>({ lang: "en", t: (k) => k, setLang: () => {} });

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("lang") as Lang | null;
      if (saved === "en" || saved === "vi") {
        setLang(saved);
      } else {
        // No saved language, set default to English
        localStorage.setItem("lang", "en");
        setLang("en");
      }
    } catch {}
  }, []);

  const t = (k: string) => DICTS[lang][k] ?? k;

  const value = useMemo(
    () => ({
      lang,
      t,
      setLang: (l: Lang) => {
        setLang(l);
        try { localStorage.setItem("lang", l); } catch {}
      },
    }),
    [lang]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export const useI18n = () => useContext(Ctx);
