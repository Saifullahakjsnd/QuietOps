import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'QuietOps — A little less on your plate', description: 'Local-first operations review. Turn shop spreadsheets into an evidence-backed fix queue.' };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) { return <html lang="en"><body>{children}</body></html>; }
