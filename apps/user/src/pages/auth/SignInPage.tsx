import { SignInForm } from "@/features/auth/SignInForm";

export function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted/20 px-4">
      <SignInForm />
    </div>
  );
}