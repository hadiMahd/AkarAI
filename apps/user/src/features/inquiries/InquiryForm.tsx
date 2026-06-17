import { useState } from "react";
import { Link } from "react-router-dom";
import { useSubmitInquiry } from "./useSubmitInquiry";
import { useUserProfile } from "@/features/profile/useUserProfile";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api/errors";

interface InquiryFormProps {
  listingId: string;
}

export function InquiryForm({ listingId }: InquiryFormProps) {
  const [message, setMessage] = useState("");
  const [clientError, setClientError] = useState<string | null>(null);
  const submitInquiry = useSubmitInquiry(listingId);
  const { data: profile, isLoading: isProfileLoading } = useUserProfile();
  const isProfileComplete = profile?.is_complete_for_leads ?? false;
  const trimmedMessage = message.trim();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isProfileLoading || !isProfileComplete) {
      return;
    }
    if (!trimmedMessage) {
      setClientError("Write a short message before sending your inquiry.");
      return;
    }
    setClientError(null);
    submitInquiry.mutate(
      {
        message: trimmedMessage,
      },
      {
        onSuccess: () => {
          setMessage("");
          setClientError(null);
        },
      }
    );
  };

  if (submitInquiry.isSuccess) {
    return (
      <Card>
        <CardContent className="pt-6">
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Your inquiry has been submitted successfully. The agency will contact you soon.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Submit Inquiry</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isProfileComplete && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <span>Complete your profile with your name and a contact method before sending a lead.</span>
                <Button asChild size="sm" variant="outline">
                  <Link to="/profile">Complete profile</Link>
                </Button>
              </AlertDescription>
            </Alert>
          )}

          <div>
            <label htmlFor="message" className="block text-sm font-medium mb-2">
              Message *
            </label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                if (clientError && e.target.value.trim()) {
                  setClientError(null);
                }
              }}
              placeholder="I'm interested in this property..."
              required
              rows={4}
            />
          </div>

          {(clientError || submitInquiry.isError) && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {clientError ??
                  getApiErrorMessage(submitInquiry.error, "inquiry.submit", {
                    fallback: "We couldn't send your inquiry. Try again in a moment.",
                  })}
              </AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            disabled={submitInquiry.isPending || isProfileLoading || !isProfileComplete || !trimmedMessage}
            className="w-full"
          >
            {submitInquiry.isPending
              ? "Submitting..."
              : isProfileLoading
                ? "Checking Profile..."
              : isProfileComplete
                ? "Submit Inquiry"
                : "Complete Profile to Submit"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
