/**
 * LoginForm component for user authentication.
 *
 * Requirements: 6.2
 * - Validates credentials and issues session token
 * - Displays generic error on failure (security)
 */

import React, { useCallback, useState } from "react";
import styles from "./styles.module.css";
import type { AuthResponse, FormErrors, LoginFormData } from "./types";

interface LoginFormProps {
  onSuccess: (response: AuthResponse) => void;
  onSwitchToRegister: () => void;
  apiEndpoint: string;
}

/**
 * Validate email format.
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * LoginForm component.
 */
export function LoginForm({
  onSuccess,
  onSwitchToRegister,
  apiEndpoint,
}: LoginFormProps): React.ReactElement {
  const [formData, setFormData] = useState<LoginFormData>({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Validate form data.
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  /**
   * Handle input change.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      const response = await fetch(`${apiEndpoint}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      if (!response.ok) {
        // Security: Generic error message (Requirement 6.4)
        throw new Error("Invalid credentials");
      }

      const data: AuthResponse = await response.json();
      onSuccess(data);
    } catch (err) {
      // Security: Don't reveal specific failure reason
      setErrors({ general: "Invalid credentials. Please try again." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className={styles.formContainer} onSubmit={handleSubmit}>
      <div className={styles.formHeader}>
        <h2 className={styles.formTitle}>Welcome Back</h2>
        <p className={styles.formSubtitle}>Sign in to continue learning</p>
      </div>

      {errors.general && (
        <div className={styles.generalError}>{errors.general}</div>
      )}

      <div className={styles.formGroup}>
        <label htmlFor="login-email" className={styles.label}>
          Email
        </label>
        <input
          id="login-email"
          type="email"
          name="email"
          className={`${styles.input} ${errors.email ? styles.inputError : ""}`}
          value={formData.email}
          onChange={handleChange}
          placeholder="you@example.com"
          autoComplete="email"
          disabled={isLoading}
        />
        {errors.email && <p className={styles.errorText}>{errors.email}</p>}
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="login-password" className={styles.label}>
          Password
        </label>
        <input
          id="login-password"
          type="password"
          name="password"
          className={`${styles.input} ${
            errors.password ? styles.inputError : ""
          }`}
          value={formData.password}
          onChange={handleChange}
          placeholder="Enter your password"
          autoComplete="current-password"
          disabled={isLoading}
        />
        {errors.password && (
          <p className={styles.errorText}>{errors.password}</p>
        )}
      </div>

      <button
        type="submit"
        className={styles.submitButton}
        disabled={isLoading}
      >
        {isLoading && <span className={styles.spinner} />}
        {isLoading ? "Signing in..." : "Sign In"}
      </button>

      <p className={styles.switchForm}>
        Don't have an account?{" "}
        <button
          type="button"
          className={styles.switchFormLink}
          onClick={onSwitchToRegister}
        >
          Create one
        </button>
      </p>
    </form>
  );
}

export default LoginForm;
