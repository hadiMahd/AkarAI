import { SignUpForm } from "@/features/auth/SignUpForm";

export function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted/20 px-4">
      <SignUpForm />
    </div>
  );
}