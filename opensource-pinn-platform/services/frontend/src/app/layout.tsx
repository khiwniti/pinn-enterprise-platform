import './globals.css';
import { Inter } from 'next/font/google';
import { CopilotKit } from '@copilotkit/react-core';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'PINN Platform - AI Physics Simulation',
  description: 'Physics-Informed Neural Networks with AI assistance',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CopilotKit 
          runtimeUrl="/api/copilotkit"
          showDevConsole={process.env.NODE_ENV === 'development'}
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}