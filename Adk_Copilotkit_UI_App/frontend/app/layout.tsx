import type { Metadata } from "next";
import "./globals.css";
import { CookieInit } from "./CookieInit";

export const metadata: Metadata = {
  title: "ADK CopilotKit App",
  description: "Deal Builder and Knowledge Q&A with ADK and CopilotKit",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CookieInit />
        {children}
      </body>
    </html>
  );
}
