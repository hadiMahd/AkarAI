import { useState } from "react";
import { useSubmitInquiry } from "./useSubmitInquiry";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api/errors";

interface InquiryFormProps {
  listingId: string;
}

export function InquiryForm({ listingId }: InquiryFormProps) {
  const [message, setMessage] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const submitInquiry = useSubmitInquiry(listingId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitInquiry.mutate(
      {
        message,
        contact_phone: contactPhone || undefined,
      },
      {
        onSuccess: () => {
          setMessage("");
          setContactPhone("");
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
          <div>
            <label htmlFor="message" className="block text-sm font-medium mb-2">
              Message *
            </label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="I'm interested in this property..."
              required
              rows={4}
            />
          </div>

          <div>
            <label htmlFor="contact_phone" className="block text-sm font-medium mb-2">
              Contact Phone (optional)
            </label>
            <Input
              id="contact_phone"
              type="tel"
              value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)}
              placeholder="+1234567890"
            />
          </div>

          {submitInquiry.isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {getApiErrorMessage(submitInquiry.error, "inquiry.submit", {
                  fallback: "We couldn't send your inquiry. Try again in a moment.",
                })}
              </AlertDescription>
            </Alert>
          )}

          <Button type="submit" disabled={submitInquiry.isPending} className="w-full">
            {submitInquiry.isPending ? "Submitting..." : "Submit Inquiry"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
