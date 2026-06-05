import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // These are Node-only libraries (fontkit, pdf/docx parsers) — don't bundle them.
  serverExternalPackages: ["@react-pdf/renderer", "unpdf", "mammoth"],
};

export default nextConfig;
