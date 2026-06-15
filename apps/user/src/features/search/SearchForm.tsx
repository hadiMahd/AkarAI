import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  AudioLines,
  Check,
  ChevronDown,
  Mic,
  Search,
  Sparkles,
} from "lucide-react";
import { useSearchIntent, useConfirmationLog } from "./useSearchIntent";
import { useVoiceSearch } from "./useVoiceSearch";
import { useListingCities } from "./useListingCities";
import type { ConfirmedSearchFilters, SearchIntentResponse } from "./useSearchIntent";
import { getApiErrorMessage } from "@/lib/api/errors";

interface SearchFilters {
  q?: string;
  purpose?: string;
  property_type?: string;
  city?: string[];
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_bathrooms?: number;
  parking?: number;
  floor?: number;
  furnishing?: string;
  min_area_size?: number;
  max_area_size?: number;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

interface SearchFormProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  onFiltersChange?: (filters: Partial<SearchFilters>) => void;
}

export function SearchForm({ filters, onFilterChange, onFiltersChange }: SearchFormProps) {
  const VOICE_PENDING_PHRASES = [
    "Transcribing your request...",
    "Extracting property filters...",
    "Checking price and room details...",
    "Preparing your search...",
  ];

  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters);
  const [isCityMenuOpen, setIsCityMenuOpen] = useState(false);
  const { data: cityOptions = [], isLoading: isCitiesLoading } = useListingCities();

  // AI search state
  const [aiMode, setAiMode] = useState(false);
  const [aiQuery, setAiQuery] = useState("");
  const [pendingIntent, setPendingIntent] = useState<SearchIntentResponse | null>(null);
  const [aiErrorMessage, setAiErrorMessage] = useState<string | null>(null);
  const [assistantNotice, setAssistantNotice] = useState<string | null>(null);
  const { mutate: extractIntent, isPending: isExtracting } = useSearchIntent();
  const { mutate: logConfirmation } = useConfirmationLog();

  // Voice search state
  const [voiceMode, setVoiceMode] = useState(false);
  const [voicePendingPhraseIndex, setVoicePendingPhraseIndex] = useState(0);
  const {
    state: voiceState,
    transcript,
    error: voiceErrorRaw,
    result: voiceResult,
    startRecording,
    stopRecording,
    discard: discardVoice,
  } = useVoiceSearch();
  const voiceErrorMessage =
    voiceState === "error" && voiceErrorRaw
      ? getApiErrorMessage(voiceErrorRaw, "search.voice", {
          fallback: "We couldn't transcribe that recording. Try again or type your search instead.",
        })
      : null;

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  useEffect(() => {
    if (voiceState !== "uploading") {
      setVoicePendingPhraseIndex(0);
      return;
    }

    const interval = window.setInterval(() => {
      setVoicePendingPhraseIndex((current) => (current + 1) % VOICE_PENDING_PHRASES.length);
    }, 1400);

    return () => window.clearInterval(interval);
  }, [voiceState]);

  useEffect(() => {
    if (!voiceResult) {
      return;
    }

    applyAssistantFilters(
      voiceResult.intent.filters,
      "voice",
      "Voice filters were applied to the search form below.",
    );
    setVoiceMode(false);
  }, [voiceResult]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ ...localFilters, page: 1 });
  };

  const handleReset = () => {
    setLocalFilters({});
    setIsCityMenuOpen(false);
    setAssistantNotice(null);
    onFilterChange({});
  };

  const assistantFiltersToSearchFilters = (
    assistantFilters: ConfirmedSearchFilters,
    existingFilters: SearchFilters,
  ): SearchFilters => {
    const nextFilters: SearchFilters = {
      q: assistantFilters.q ?? assistantFilters.location ?? undefined,
      purpose: assistantFilters.listing_purpose ?? undefined,
      property_type: assistantFilters.property_type ?? undefined,
      city: assistantFilters.city ? [assistantFilters.city] : undefined,
      min_price: assistantFilters.min_price ?? undefined,
      max_price: assistantFilters.max_price ?? undefined,
      min_bedrooms: assistantFilters.bedrooms ?? undefined,
      min_bathrooms: assistantFilters.bathrooms ?? undefined,
      parking: assistantFilters.parking ?? undefined,
      floor: assistantFilters.floor ?? undefined,
      furnishing: assistantFilters.furnishing ?? undefined,
      min_area_size: assistantFilters.min_area_size ?? undefined,
      max_area_size: assistantFilters.max_area_size ?? undefined,
      sort_by: existingFilters.sort_by || "created_at",
      sort_order: existingFilters.sort_order || "desc",
      page: 1,
      page_size: existingFilters.page_size || 12,
    };

    if (assistantFilters.sort === "oldest") {
      nextFilters.sort_by = "created_at";
      nextFilters.sort_order = "asc";
    } else if (assistantFilters.sort === "newest") {
      nextFilters.sort_by = "created_at";
      nextFilters.sort_order = "desc";
    } else if (assistantFilters.sort === "price_asc") {
      nextFilters.sort_by = "price";
      nextFilters.sort_order = "asc";
    } else if (assistantFilters.sort === "price_desc") {
      nextFilters.sort_by = "price";
      nextFilters.sort_order = "desc";
    } else if (assistantFilters.sort === "area_size_asc") {
      nextFilters.sort_by = "area_size";
      nextFilters.sort_order = "asc";
    } else if (assistantFilters.sort === "area_size_desc") {
      nextFilters.sort_by = "area_size";
      nextFilters.sort_order = "desc";
    }

    return nextFilters;
  };

  const applyAssistantFilters = (
    assistantFilters: ConfirmedSearchFilters,
    sourceMode: "ai_text" | "voice",
    notice: string,
  ) => {
    const nextFilters = assistantFiltersToSearchFilters(assistantFilters, localFilters);
    setLocalFilters(nextFilters);
    setAssistantNotice(notice);
    logConfirmation({ source_mode: sourceMode, confirmed_filters: assistantFilters });
    onFilterChange(nextFilters);
  };

  const availableCities = Array.from(
    new Set([...(cityOptions ?? []), ...(localFilters.city ?? [])]),
  ).sort((left, right) => left.localeCompare(right));

  const selectedCities = localFilters.city || [];
  const cityButtonLabel =
    selectedCities.length === 0
      ? isCitiesLoading && availableCities.length === 0
        ? "Loading cities..."
        : "Choose cities"
      : selectedCities.length === 1
        ? selectedCities[0]
        : `${selectedCities.length} cities selected`;

  const toggleCity = (city: string, checked: boolean) => {
    const nextCities = checked
      ? Array.from(new Set([...selectedCities, city]))
      : selectedCities.filter((value) => value !== city);
    setLocalFilters({
      ...localFilters,
      city: nextCities.length > 0 ? nextCities : undefined,
    });
  };

  return (
    <div className="space-y-4">
      {/* Mode toggle buttons */}
      <div className="grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => { setAiMode(!aiMode); setVoiceMode(false); }}
          className={[
            "flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors",
            aiMode
              ? "border-sky-500 bg-sky-50 text-sky-950"
              : "border-border bg-background text-foreground hover:border-sky-200 hover:bg-sky-50/60",
          ].join(" ")}
          data-testid="ai-search-toggle"
        >
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="space-y-1">
            <span className="block text-sm font-medium">
              {aiMode ? "Manual search" : "Search with AI"}
            </span>
            <span className="block text-xs text-muted-foreground">
              Type a natural request and let the assistant map it to filters.
            </span>
          </span>
        </button>
        <button
          type="button"
          onClick={() => { setVoiceMode(!voiceMode); setAiMode(false); }}
          data-testid="voice-search-toggle"
          className={[
            "flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors",
            voiceMode
              ? "border-emerald-500 bg-emerald-50 text-emerald-950"
              : "border-border bg-background text-foreground hover:border-emerald-200 hover:bg-emerald-50/60",
          ].join(" ")}
        >
          <AudioLines className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="space-y-1">
            <span className="block text-sm font-medium">
              {voiceMode ? "Text search" : "Voice search"}
            </span>
            <span className="block text-xs text-muted-foreground">
              Speak naturally and we will turn it into listing filters.
            </span>
          </span>
        </button>
      </div>

      {/* AI Search Panel */}
      {aiMode && (
        <div data-testid="ai-search-panel" className="space-y-2">
          <Input
            placeholder="Describe what you're looking for..."
            value={aiQuery}
            onChange={(e) => setAiQuery(e.target.value)}
            data-testid="ai-search-input"
          />
          <Button
            onClick={() => {
              setAiErrorMessage(null);
              extractIntent(aiQuery, {
                onSuccess: (data) => {
                  setPendingIntent(data);
                  setAiErrorMessage(null);
                  applyAssistantFilters(
                    data.intent.filters,
                    "ai_text",
                    "AI filters were applied to the search form below.",
                  );
                  if (!data.intent.unclear_location) {
                    setAiMode(false);
                  }
                },
                onError: (error) => {
                  setPendingIntent(null);
                  setAiErrorMessage(
                    getApiErrorMessage(error, "search.intent", {
                      fallback: "We couldn't analyze that. Try again or use the manual filters.",
                    }),
                  );
                },
              });
            }}
            disabled={isExtracting || !aiQuery.trim()}
            data-testid="ai-search-submit"
          >
            {isExtracting ? "Analyzing..." : "Find properties"}
          </Button>
          {aiErrorMessage && (
            <p data-testid="ai-search-error" role="alert" className="text-sm text-destructive">
              {aiErrorMessage}
            </p>
          )}

          {pendingIntent?.intent.unclear_location && (
            <div
              data-testid="ai-confirmation-panel"
              className="mt-3 p-3 border rounded-lg bg-muted/30"
            >
              <div
                data-testid="vague-location-warning"
                className="text-sm text-amber-600"
              >
                Vague location: "{pendingIntent.intent.unclear_location.phrase}". Adjust the city field below,
                or continue without location.
                <Button
                  variant="ghost"
                  size="sm"
                  data-testid="continue-without-location"
                  onClick={() => {
                    const filtersWithoutLocation = {
                      ...pendingIntent.intent.filters,
                      city: undefined,
                      location: undefined,
                    };
                    setPendingIntent({
                      ...pendingIntent,
                      intent: {
                        ...pendingIntent.intent,
                        filters: filtersWithoutLocation,
                        unclear_location: undefined,
                      },
                    });
                    applyAssistantFilters(
                      filtersWithoutLocation,
                      "ai_text",
                      "AI filters were applied without a location. Choose the city manually below.",
                    );
                    setAiMode(false);
                  }}
                >
                  Continue without location
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Voice Search Panel */}
      {voiceMode && (
        <div data-testid="voice-search-panel" className="mt-2">
          {voiceState === "idle" && (
            <Button onClick={startRecording} data-testid="start-recording" className="gap-2">
              <Mic className="h-4 w-4" />
              Start voice search
            </Button>
          )}
          {voiceState === "recording" && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-500 animate-pulse">Recording...</span>
              <Button onClick={stopRecording} variant="outline" data-testid="stop-recording">
                Stop
              </Button>
              <Button onClick={discardVoice} variant="ghost" data-testid="discard-recording">
                Discard
              </Button>
            </div>
          )}
          {voiceState === "uploading" && (
            <div
              data-testid="voice-uploading-status"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-2 text-sm text-muted-foreground"
            >
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
              {VOICE_PENDING_PHRASES[voicePendingPhraseIndex]}
            </div>
          )}
          {voiceErrorMessage && (
            <div
              data-testid="voice-search-error"
              role="alert"
              className="mt-2 flex items-center justify-between gap-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive"
            >
              <span>{voiceErrorMessage}</span>
              <Button
                onClick={discardVoice}
                variant="ghost"
                size="sm"
                data-testid="voice-error-dismiss"
              >
                Dismiss
              </Button>
            </div>
          )}
          {transcript && (
            <div data-testid="voice-transcript" className="mt-2 p-2 bg-muted rounded text-sm">
              <span className="font-medium">Transcript: </span>
              {transcript}
              <button
                onClick={discardVoice}
                data-testid="discard-voice"
                className="ml-2 text-xs text-muted-foreground underline"
              >
                Discard
              </button>
            </div>
          )}
          {voiceResult && assistantNotice && (
            <p data-testid="voice-applied-notice" className="mt-2 text-sm text-muted-foreground">
              {assistantNotice}
            </p>
          )}
        </div>
      )}

      {/* Manual Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        {assistantNotice && (
          <div
            data-testid="assistant-applied-notice"
            className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground"
          >
            {assistantNotice}
          </div>
        )}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="q">Search</Label>
              <Input
                id="q"
                placeholder="Search listings..."
                value={localFilters.q || ""}
                onChange={(e) => setLocalFilters({ ...localFilters, q: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="purpose">Purpose</Label>
              <select
                id="purpose"
                value={localFilters.purpose || ""}
                onChange={(e) => setLocalFilters({ ...localFilters, purpose: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">All</option>
                <option value="sale">For Sale</option>
                <option value="rent">For Rent</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="property_type">Property Type</Label>
              <select
                id="property_type"
                value={localFilters.property_type || ""}
                onChange={(e) =>
                  setLocalFilters({ ...localFilters, property_type: e.target.value })
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">All Types</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="villa">Villa</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="city-trigger">City</Label>
              <div className="relative">
                <Button
                  id="city-trigger"
                  type="button"
                  variant="outline"
                  aria-label="City"
                  aria-expanded={isCityMenuOpen}
                  className="flex h-10 w-full items-center justify-between px-3 text-sm font-normal"
                  disabled={isCitiesLoading && availableCities.length === 0}
                  data-testid="city-filter-trigger"
                  onClick={() => setIsCityMenuOpen((current) => !current)}
                >
                  <span className="truncate">{cityButtonLabel}</span>
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-muted-foreground" />
                </Button>
                {isCityMenuOpen && (
                  <div
                    className="absolute z-20 mt-2 w-full rounded-md border bg-popover p-2 text-popover-foreground shadow-md"
                    data-testid="city-filter-panel"
                  >
                    <div className="px-2 py-1.5 text-sm font-semibold">Select cities</div>
                    {selectedCities.length > 0 && (
                      <>
                        <button
                          type="button"
                          className="flex w-full items-center rounded-sm px-2 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                          onClick={() => setLocalFilters({ ...localFilters, city: undefined })}
                          data-testid="clear-city-filters"
                        >
                          Clear all
                        </button>
                        <div className="-mx-1 my-1 h-px bg-muted" />
                      </>
                    )}
                    <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
                      {availableCities.map((city) => (
                        <label
                          key={city}
                          className="flex cursor-pointer items-center gap-3 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCities.includes(city)}
                            onChange={(event) => toggleCity(city, event.target.checked)}
                            className="h-4 w-4 rounded border-border"
                          />
                          <span>{city}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {selectedCities.length > 0 && (
                <div className="flex flex-wrap gap-2" data-testid="selected-city-chips">
                  {selectedCities.map((city) => (
                    <span
                      key={city}
                      className="inline-flex items-center gap-1 rounded-md border border-border bg-muted/40 px-2 py-1 text-xs text-foreground"
                    >
                      <Check className="h-3 w-3" />
                      {city}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {isCitiesLoading && availableCities.length === 0
                  ? "Loading cities..."
                  : "Open the list and choose one or more cities."}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="min_price">Min Price</Label>
              <Input
                id="min_price"
                type="number"
                placeholder="Min"
                value={localFilters.min_price || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    min_price: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_price">Max Price</Label>
              <Input
                id="max_price"
                type="number"
                placeholder="Max"
                value={localFilters.max_price || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    max_price: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="min_bedrooms">Min Bedrooms</Label>
              <Input
                id="min_bedrooms"
                type="number"
                placeholder="Min"
                value={localFilters.min_bedrooms || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    min_bedrooms: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="min_bathrooms">Min Bathrooms</Label>
              <Input
                id="min_bathrooms"
                type="number"
                placeholder="Min"
                value={localFilters.min_bathrooms || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    min_bathrooms: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>

            {/* Parking */}
            <div className="space-y-2">
              <Label htmlFor="parking">Parking spaces</Label>
              <Input
                id="parking"
                type="number"
                min={0}
                placeholder="Min parking"
                value={localFilters.parking ?? ""}
                onChange={(e) =>
                  setLocalFilters((prev) => ({
                    ...prev,
                    parking: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />
            </div>

            {/* Floor */}
            <div className="space-y-2">
              <Label htmlFor="floor">Floor</Label>
              <Input
                id="floor"
                type="number"
                min={0}
                placeholder="Floor number"
                value={localFilters.floor ?? ""}
                onChange={(e) =>
                  setLocalFilters((prev) => ({
                    ...prev,
                    floor: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="furnishing">Furnishing</Label>
              <select
                id="furnishing"
                value={localFilters.furnishing || ""}
                onChange={(e) =>
                  setLocalFilters({ ...localFilters, furnishing: e.target.value || undefined })
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Any</option>
                <option value="furnished">Furnished</option>
                <option value="semi_furnished">Semi Furnished</option>
                <option value="unfurnished">Unfurnished</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="min_area_size">Min Area</Label>
              <Input
                id="min_area_size"
                type="number"
                placeholder="Min area"
                value={localFilters.min_area_size || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    min_area_size: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_area_size">Max Area</Label>
              <Input
                id="max_area_size"
                type="number"
                placeholder="Max area"
                value={localFilters.max_area_size || ""}
                onChange={(e) =>
                  setLocalFilters({
                    ...localFilters,
                    max_area_size: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>
          </div>

          <div className="flex gap-2">
            <Button type="submit">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button type="button" variant="outline" onClick={handleReset}>
              Reset
            </Button>
          </div>
        </form>
    </div>
  );
}
