import type { Metadata } from "next";
import LayoutShell from "./components/LayoutShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "NUCTECS",
  description: "Northwestern Course Search",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
        <body>
            <LayoutShell>{children}</LayoutShell>
        </body>
    </html>
  );
}
