/**
 * RegistrationForm component for user registration with background questions.
 *
 * Requirements: 6.1, 6.5
 * - Collects email, password, and background information
 * - Stores user background preferences in database
 */

import { useAuth } from "@site/src/components/AuthProvider";
import React, { useCallback, useState } from "react";
import styles from "./styles.module.css";
import type { AuthResponse, FormErrors, RegistrationFormData } from "./types";

interface RegistrationFormProps {
  onSuccess: (response: AuthResponse) => void;
  onSwitchToLogin: () => void;
  apiEndpoint: string;
}

const EXPERIENCE_LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const COMMON_LANGUAGES = ["Python", "JavaScript", "C++", "Java", "Rust", "Go"];

/**
 * Validate email format.
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * RegistrationForm component.
 */
export function RegistrationForm({
  onSuccess,
  onSwitchToLogin,
  apiEndpoint,
}: RegistrationFormProps): React.ReactElement {
  const { register } = useAuth();
  const [formData, setFormData] = useState<RegistrationFormData>({
    email: "",
    password: "",
    confirmPassword: "",
    background: {
      software_experience: "beginner",
      hardware_experience: "beginner",
      programming_languages: [],
      robotics_experience: false,
      ai_experience: false,
    },
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [languageInput, setLanguageInput] = useState("");

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
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  /**
   * Handle input change for text fields.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  /**
   * Handle select change for experience levels.
   */
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      background: {
        ...prev.background,
        [name]: value as "beginner" | "intermediate" | "advanced",
      },
    }));
  };

  /**
   * Handle checkbox change for boolean fields.
   */
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      background: {
        ...prev.background,
        [name]: checked,
      },
    }));
  };

  /**
   * Add a programming language tag.
   */
  const addLanguage = (language: string) => {
    const trimmed = language.trim();
    if (
      trimmed &&
      !formData.background.programming_languages.includes(trimmed)
    ) {
      setFormData((prev) => ({
        ...prev,
        background: {
          ...prev.background,
          programming_languages: [
            ...prev.background.programming_languages,
            trimmed,
          ],
        },
      }));
    }
    setLanguageInput("");
  };

  /**
   * Remove a programming language tag.
   */
  const removeLanguage = (language: string) => {
    setFormData((prev) => ({
      ...prev,
      background: {
        ...prev.background,
        programming_languages: prev.background.programming_languages.filter(
          (l) => l !== language
        ),
      },
    }));
  };

  /**
   * Handle language input keydown.
   */
  const handleLanguageKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addLanguage(languageInput);
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
      // Use the register function from AuthProvider which handles state
      await register(formData.email, formData.password, formData.background);
      onSuccess({} as AuthResponse); // Just to close the modal
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Registration failed. Please try again.";
      setErrors({ general: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className={styles.formContainer} onSubmit={handleSubmit}>
      <div className={styles.formHeader}>
        <h2 className={styles.formTitle}>Create Account</h2>
        <p className={styles.formSubtitle}>
          Join us to start learning Physical AI
        </p>
      </div>

      {errors.general && (
        <div className={styles.generalError}>{errors.general}</div>
      )}

      {/* Email field */}
      <div className={styles.formGroup}>
        <label htmlFor="register-email" className={styles.label}>
          Email
        </label>
        <input
          id="register-email"
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

      {/* Password field */}
      <div className={styles.formGroup}>
        <label htmlFor="register-password" className={styles.label}>
          Password
        </label>
        <input
          id="register-password"
          type="password"
          name="password"
          className={`${styles.input} ${
            errors.password ? styles.inputError : ""
          }`}
          value={formData.password}
          onChange={handleChange}
          placeholder="At least 8 characters"
          autoComplete="new-password"
          disabled={isLoading}
        />
        {errors.password && (
          <p className={styles.errorText}>{errors.password}</p>
        )}
      </div>

      {/* Confirm password field */}
      <div className={styles.formGroup}>
        <label htmlFor="register-confirm-password" className={styles.label}>
          Confirm Password
        </label>
        <input
          id="register-confirm-password"
          type="password"
          name="confirmPassword"
          className={`${styles.input} ${
            errors.confirmPassword ? styles.inputError : ""
          }`}
          value={formData.confirmPassword}
          onChange={handleChange}
          placeholder="Confirm your password"
          autoComplete="new-password"
          disabled={isLoading}
        />
        {errors.confirmPassword && (
          <p className={styles.errorText}>{errors.confirmPassword}</p>
        )}
      </div>

      {/* Background Questions Section */}
      <h3 className={styles.sectionTitle}>Your Background</h3>

      {/* Software Experience */}
      <div className={styles.formGroup}>
        <label htmlFor="software-experience" className={styles.label}>
          Software Development Experience
        </label>
        <select
          id="software-experience"
          name="software_experience"
          className={styles.select}
          value={formData.background.software_experience}
          onChange={handleSelectChange}
          disabled={isLoading}
        >
          {EXPERIENCE_LEVELS.map((level) => (
            <option key={level.value} value={level.value}>
              {level.label}
            </option>
          ))}
        </select>
      </div>

      {/* Hardware Experience */}
      <div className={styles.formGroup}>
        <label htmlFor="hardware-experience" className={styles.label}>
          Hardware/Electronics Experience
        </label>
        <select
          id="hardware-experience"
          name="hardware_experience"
          className={styles.select}
          value={formData.background.hardware_experience}
          onChange={handleSelectChange}
          disabled={isLoading}
        >
          {EXPERIENCE_LEVELS.map((level) => (
            <option key={level.value} value={level.value}>
              {level.label}
            </option>
          ))}
        </select>
      </div>

      {/* Programming Languages */}
      <div className={styles.formGroup}>
        <label className={styles.label}>Programming Languages</label>
        <div className={styles.tagsContainer}>
          {formData.background.programming_languages.map((lang) => (
            <span key={lang} className={styles.tag}>
              {lang}
              <button
                type="button"
                className={styles.tagRemove}
                onClick={() => removeLanguage(lang)}
                disabled={isLoading}
                aria-label={`Remove ${lang}`}
              >
                ×
              </button>
            </span>
          ))}
          <input
            type="text"
            className={styles.tagInput}
            value={languageInput}
            onChange={(e) => setLanguageInput(e.target.value)}
            onKeyDown={handleLanguageKeyDown}
            onBlur={() => languageInput && addLanguage(languageInput)}
            placeholder="Type and press Enter"
            disabled={isLoading}
          />
        </div>
        <div
          style={{
            marginTop: "8px",
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
          }}
        >
          {COMMON_LANGUAGES.filter(
            (lang) => !formData.background.programming_languages.includes(lang)
          ).map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => addLanguage(lang)}
              disabled={isLoading}
              style={{
                padding: "2px 8px",
                fontSize: "12px",
                background: "var(--ifm-color-emphasis-100)",
                border: "1px solid var(--ifm-color-emphasis-300)",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              + {lang}
            </button>
          ))}
        </div>
      </div>

      {/* Experience Checkboxes */}
      <div className={styles.formGroup}>
        <label className={styles.label}>Prior Experience</label>
        <div className={styles.checkboxGroup}>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              name="robotics_experience"
              className={styles.checkbox}
              checked={formData.background.robotics_experience}
              onChange={handleCheckboxChange}
              disabled={isLoading}
            />
            I have experience with robotics
          </label>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              name="ai_experience"
              className={styles.checkbox}
              checked={formData.background.ai_experience}
              onChange={handleCheckboxChange}
              disabled={isLoading}
            />
            I have experience with AI/Machine Learning
          </label>
        </div>
      </div>

      <button
        type="submit"
        className={styles.submitButton}
        disabled={isLoading}
      >
        {isLoading && <span className={styles.spinner} />}
        {isLoading ? "Creating Account..." : "Create Account"}
      </button>

      <p className={styles.switchForm}>
        Already have an account?{" "}
        <button
          type="button"
          className={styles.switchFormLink}
          onClick={onSwitchToLogin}
        >
          Sign in
        </button>
      </p>
    </form>
  );
}

export default RegistrationForm;
