import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import ProfilePage from "./pages/ProfilePage";
import EditProfilePage from "./pages/EditProfilePage";
import BlockedUsersPage from "./pages/BlockedUsersPage";
import ContactSettingsPage from "./pages/ContactSettingsPage";
import CreatePostPage from "./pages/CreatePostPage";
import PostDetailPage from "./pages/PostDetailPage";
import EditPostPage from "./pages/EditPostPage";
import SavedPostsPage from "./pages/SavedPostsPage";
import ExplorePage from "./pages/ExplorePage";
import SearchPage from "./pages/SearchPage";
import CreateStoryPage from "./pages/CreateStoryPage";
import MessagesPage from "./pages/MessagesPage";
import ConversationPage from "./pages/ConversationPage";
import NotificationsPage from "./pages/NotificationsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="explore" element={<ExplorePage />} />
        <Route path="messages" element={<MessagesPage />} />
        <Route path="messages/:id" element={<ConversationPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="create" element={<CreatePostPage />} />
        <Route path="stories/new" element={<CreateStoryPage />} />
        <Route path="p/:id" element={<PostDetailPage />} />
        <Route path="p/:id/edit" element={<EditPostPage />} />
        <Route path="saved" element={<SavedPostsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="u/:username" element={<ProfilePage />} />
        <Route path="accounts/edit" element={<EditProfilePage />} />
        <Route path="accounts/blocked" element={<BlockedUsersPage />} />
        <Route path="accounts/contact" element={<ContactSettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
