export interface RecruiterHint {
  domain: string;
  pattern: string; // e.g. "first@stripe.com" or "first.last@meesho.com"
}

// Email patterns for known companies (best-effort; verify before sending)
const HINTS: Record<string, RecruiterHint> = {
  "Meesho":         { domain: "meesho.com",       pattern: "first@meesho.com" },
  "PhonePe":        { domain: "phonepe.com",       pattern: "first.last@phonepe.com" },
  "CRED":           { domain: "cred.club",         pattern: "first@cred.club" },
  "Groww":          { domain: "groww.in",          pattern: "first.last@groww.in" },
  "Razorpay":       { domain: "razorpay.com",      pattern: "first.last@razorpay.com" },
  "Dream11":        { domain: "dream11.com",       pattern: "first.last@dream11.com" },
  "Fampay":         { domain: "fampay.in",         pattern: "first@fampay.in" },
  "Porter":         { domain: "porter.in",         pattern: "first.last@porter.in" },
  "Zeta":           { domain: "zeta.tech",         pattern: "first.last@zeta.tech" },
  "Fi Money":       { domain: "fi.money",          pattern: "first@fi.money" },
  "DevRev":         { domain: "devrev.ai",         pattern: "first@devrev.ai" },
  "Atlan":          { domain: "atlan.com",         pattern: "first@atlan.com" },
  "HackerRank":     { domain: "hackerrank.com",    pattern: "first.last@hackerrank.com" },
  "Postman":        { domain: "postman.com",       pattern: "first.last@postman.com" },
  "Stripe":         { domain: "stripe.com",        pattern: "first@stripe.com" },
  "Airbnb":         { domain: "airbnb.com",        pattern: "first@airbnb.com" },
  "OpenAI":         { domain: "openai.com",        pattern: "first@openai.com" },
  "Anthropic":      { domain: "anthropic.com",     pattern: "first@anthropic.com" },
  "Perplexity":     { domain: "perplexity.ai",     pattern: "first@perplexity.ai" },
  "Databricks":     { domain: "databricks.com",    pattern: "first.last@databricks.com" },
  "Datadog":        { domain: "datadoghq.com",     pattern: "first.last@datadoghq.com" },
  "Cloudflare":     { domain: "cloudflare.com",    pattern: "first.last@cloudflare.com" },
  "Figma":          { domain: "figma.com",         pattern: "first@figma.com" },
  "Notion":         { domain: "notion.so",         pattern: "first@notion.so" },
  "Supabase":       { domain: "supabase.io",       pattern: "first@supabase.io" },
  "PostHog":        { domain: "posthog.com",       pattern: "first@posthog.com" },
  "Cursor":         { domain: "cursor.sh",         pattern: "first@cursor.sh" },
  "Replit":         { domain: "replit.com",        pattern: "first@replit.com" },
  "Linear":         { domain: "linear.app",        pattern: "first@linear.app" },
  "Vercel":         { domain: "vercel.com",        pattern: "first@vercel.com" },
  "Render":         { domain: "render.com",        pattern: "first@render.com" },
  "Grafana":        { domain: "grafana.com",       pattern: "first.last@grafana.com" },
  "Fivetran":       { domain: "fivetran.com",      pattern: "first.last@fivetran.com" },
  "MongoDB":        { domain: "mongodb.com",       pattern: "first.last@mongodb.com" },
  "Elastic":        { domain: "elastic.co",        pattern: "first.last@elastic.co" },
  "Ramp":           { domain: "ramp.com",          pattern: "first@ramp.com" },
  "Brex":           { domain: "brex.com",          pattern: "first@brex.com" },
  "Zscaler":        { domain: "zscaler.com",       pattern: "first.last@zscaler.com" },
  "Scale AI":       { domain: "scale.com",         pattern: "first@scale.com" },
  "ElevenLabs":     { domain: "elevenlabs.io",     pattern: "first@elevenlabs.io" },
  "Glean":          { domain: "glean.com",         pattern: "first@glean.com" },
  "Hightouch":      { domain: "hightouch.com",     pattern: "first@hightouch.com" },
  "Watershed":      { domain: "watershed.com",     pattern: "first@watershed.com" },
  "Temporal":       { domain: "temporal.io",       pattern: "first@temporal.io" },
  "Samsara":        { domain: "samsara.com",       pattern: "first.last@samsara.com" },
  "Twilio":         { domain: "twilio.com",        pattern: "first.last@twilio.com" },
  "GitLab":         { domain: "gitlab.com",        pattern: "first.last@gitlab.com" },
  "Asana":          { domain: "asana.com",         pattern: "first.last@asana.com" },
  "Lyft":           { domain: "lyft.com",          pattern: "first.last@lyft.com" },
  "Discord":        { domain: "discord.com",       pattern: "first@discord.com" },
  "Reddit":         { domain: "reddit.com",        pattern: "first.last@reddit.com" },
  "Airtable":       { domain: "airtable.com",      pattern: "first.last@airtable.com" },
  "Amplitude":      { domain: "amplitude.com",     pattern: "first.last@amplitude.com" },
  "Okta":           { domain: "okta.com",          pattern: "first.last@okta.com" },
  "New Relic":      { domain: "newrelic.com",      pattern: "first.last@newrelic.com" },
  "Rubrik":         { domain: "rubrik.com",        pattern: "first.last@rubrik.com" },
  "SingleStore":    { domain: "singlestore.com",   pattern: "first.last@singlestore.com" },
  "Yugabyte":       { domain: "yugabyte.com",      pattern: "first.last@yugabyte.com" },
  "CockroachDB":    { domain: "cockroachlabs.com", pattern: "first.last@cockroachlabs.com" },
};

export function getHint(company: string): RecruiterHint | null {
  return HINTS[company] ?? null;
}

export function linkedInSearchUrl(company: string): string {
  return `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(`recruiter ${company} India`)}&network=%5B%22F%22%2C%22S%22%5D`;
}
