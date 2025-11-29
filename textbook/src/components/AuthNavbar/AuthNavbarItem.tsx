/**
 * AuthNavbarItem component for displaying auth buttons in the navbar.
 *
 * Requirements: 6.1, 6.2
 * - Add login/register buttons to navbar
 * - Show user status in header
 */

import React, { useState } from "react";
import { LoginForm, RegistrationForm } from "../AuthForms";
import type { AuthResponse } from "../AuthProvider";
import { useAuth } from "../AuthProvider";
import styles from "./styles.module.css";

// API endpoint configuration
import { API_BASE_URL } from "@site/src/config";
const API_ENDPOINT = API_BASE_URL;

type ModalType = "login" | "register" | null;

/**
 * AuthNavbarItem component.
 */
export function AuthNavbarItem(): React.ReactElement {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [modalType, setModalType] = useState<ModalType>(null);

  /**
   * Handle successful authentication.
   */
  const handleAuthSuccess = (_response: AuthResponse) => {
    setModalType(null);
  };

  /**
   * Handle logout click.
   */
  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Ignore errors, user is logged out locally
    }
  };

  /**
   * Close modal.
   */
  const closeModal = () => {
    setModalType(null);
  };

  /**
   * Handle modal backdrop click.
   */
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeModal();
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className={styles.authContainer}>
        <span className={styles.loadingText}>Loading...</span>
      </div>
    );
  }

  // Show authenticated state
  if (isAuthenticated && user) {
    return (
      <div className={styles.authContainer}>
        <span className={styles.userEmail}>{user.email}</span>
        <button
          type="button"
          className={styles.logoutButton}
          onClick={handleLogout}
        >
          Sign Out
        </button>
      </div>
    );
  }

  // Show unauthenticated state
  return (
    <>
      <div className={styles.authContainer}>
        <button
          type="button"
          className={styles.loginButton}
          onClick={() => setModalType("login")}
        >
          Sign In
        </button>
        <button
          type="button"
          className={styles.registerButton}
          onClick={() => setModalType("register")}
        >
          Sign Up
        </button>
      </div>

      {/* Auth Modal */}
      {modalType && (
        <div
          className={styles.modalOverlay}
          onClick={handleBackdropClick}
          role="dialog"
          aria-modal="true"
          aria-labelledby="auth-modal-title"
        >
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <button
                type="button"
                className={styles.closeButton}
                onClick={closeModal}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            {modalType === "login" ? (
              <LoginForm
                apiEndpoint={API_ENDPOINT}
                onSuccess={handleAuthSuccess}
                onSwitchToRegister={() => setModalType("register")}
              />
            ) : (
              <RegistrationForm
                apiEndpoint={API_ENDPOINT}
                onSuccess={handleAuthSuccess}
                onSwitchToLogin={() => setModalType("login")}
              />
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default AuthNavbarItem;
