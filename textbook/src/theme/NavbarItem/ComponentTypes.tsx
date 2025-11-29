/**
 * Custom NavbarItem component types for Docusaurus.
 * This adds support for custom navbar item types like 'authButtons'.
 *
 * Requirements: 6.1, 6.2
 */

import { AuthNavbarItem } from "@site/src/components/AuthNavbar";
import ComponentTypes from "@theme-original/NavbarItem/ComponentTypes";

export default {
  ...ComponentTypes,
  "custom-authButtons": AuthNavbarItem,
};
