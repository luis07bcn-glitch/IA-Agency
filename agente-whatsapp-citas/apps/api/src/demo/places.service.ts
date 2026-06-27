import { Injectable, Logger } from '@nestjs/common';

const PLACES_BASE = 'https://places.googleapis.com/v1';

// Fields requested when searching by text (cheap field mask).
const SEARCH_FIELDS = [
  'places.id',
  'places.displayName',
  'places.formattedAddress',
  'places.primaryTypeDisplayName',
  'places.businessStatus',
].join(',');

// Rich field mask used to build the agent profile from a single place.
const DETAILS_FIELDS = [
  'displayName',
  'formattedAddress',
  'nationalPhoneNumber',
  'internationalPhoneNumber',
  'websiteUri',
  'regularOpeningHours',
  'editorialSummary',
  'primaryTypeDisplayName',
  'primaryType',
  'reviews',
  'rating',
  'userRatingCount',
  'googleMapsUri',
  'businessStatus',
].join(',');

export interface PlaceReview {
  author: string;
  rating: number;
  text: string;
  when: string | null;
}

export interface PlaceDetails {
  placeId: string;
  name: string;
  address: string | null;
  phone: string | null;
  website: string | null;
  googleMapsUri: string | null;
  primaryType: string | null;
  rating: number | null;
  userRatingCount: number;
  editorialSummary: string | null;
  /** Human-readable opening-hours lines, localized (es). */
  openingHours: string[];
  reviews: PlaceReview[];
}

/**
 * Thin wrapper around Google Places API (New). Reuses the same
 * GOOGLE_PLACES_API_KEY as ProspectorIA. Used by the "instant demo" to look up a
 * business by name + city and pull everything needed to bootstrap an agent.
 */
@Injectable()
export class PlacesService {
  private readonly logger = new Logger('PlacesService');

  private get apiKey(): string | null {
    return process.env.GOOGLE_PLACES_API_KEY || null;
  }

  get isConfigured(): boolean {
    return !!this.apiKey;
  }

  /** Finds the single best-matching place for a free-text query (e.g. "Bar Pepe Madrid"). */
  async findTopMatch(query: string): Promise<{ placeId: string; name: string } | null> {
    if (!this.apiKey) throw new Error('GOOGLE_PLACES_API_KEY no configurada.');

    const res = await fetch(`${PLACES_BASE}/places:searchText`, {
      method: 'POST',
      headers: {
        'X-Goog-Api-Key': this.apiKey,
        'X-Goog-FieldMask': SEARCH_FIELDS,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ textQuery: query, languageCode: 'es', pageSize: 5 }),
    });

    const data = (await res.json()) as {
      places?: { id: string; displayName?: { text?: string } }[];
      error?: { message?: string; status?: string };
    };

    if (!res.ok) {
      throw new Error(
        `Google Places: ${data.error?.status ?? res.status} — ${data.error?.message ?? ''}`,
      );
    }

    const top = data.places?.[0];
    if (!top) return null;
    return { placeId: top.id, name: top.displayName?.text ?? query };
  }

  /** Pulls rich details for a place id and normalizes them for the agent builder. */
  async getDetails(placeId: string): Promise<PlaceDetails> {
    if (!this.apiKey) throw new Error('GOOGLE_PLACES_API_KEY no configurada.');

    const res = await fetch(
      `${PLACES_BASE}/places/${encodeURIComponent(placeId)}?languageCode=es`,
      {
        headers: {
          'X-Goog-Api-Key': this.apiKey,
          'X-Goog-FieldMask': DETAILS_FIELDS,
        },
      },
    );

    const r = (await res.json()) as any;
    if (!res.ok) {
      throw new Error(
        `Google Places (details): ${r?.error?.status ?? res.status} — ${r?.error?.message ?? ''}`,
      );
    }

    const reviews: PlaceReview[] = (r.reviews ?? [])
      .slice(0, 8)
      .map((rv: any) => ({
        author: rv.authorAttribution?.displayName ?? 'Anónimo',
        rating: rv.rating ?? 0,
        text:
          typeof rv.text === 'object' ? (rv.text?.text ?? '') : String(rv.text ?? ''),
        when: rv.relativePublishTimeDescription ?? null,
      }))
      .filter((rv: PlaceReview) => rv.text.trim().length > 0);

    return {
      placeId,
      name: r.displayName?.text ?? '',
      address: r.formattedAddress ?? null,
      phone: r.nationalPhoneNumber ?? r.internationalPhoneNumber ?? null,
      website: r.websiteUri ?? null,
      googleMapsUri: r.googleMapsUri ?? null,
      primaryType: r.primaryTypeDisplayName?.text ?? r.primaryType ?? null,
      rating: r.rating ?? null,
      userRatingCount: r.userRatingCount ?? 0,
      editorialSummary: r.editorialSummary?.text ?? null,
      openingHours: r.regularOpeningHours?.weekdayDescriptions ?? [],
      reviews,
    };
  }
}
