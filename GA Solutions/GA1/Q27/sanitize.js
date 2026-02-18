// Next.js API route: /api/sanitize
// Implements input validation, sanitization, PII redaction, SQL injection blocking,
// HTML/JS removal and output escaping. Returns structured JSON responses.

const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX = 10; // max requests per IP per window
const rateMap = new Map();

function now() {
  return Date.now();
}

function trackRate(ip) {
  const entry = rateMap.get(ip) || { count: 0, start: now() };
  const elapsed = now() - entry.start;
  if (elapsed > RATE_LIMIT_WINDOW_MS) {
    entry.count = 1;
    entry.start = now();
  } else {
    entry.count += 1;
  }
  rateMap.set(ip, entry);
  return entry.count <= RATE_LIMIT_MAX;
}

// Basic HTML/JS stripper: remove <script>...</script>, inline event handlers, javascript: URIs
function stripDangerousHtml(input) {
  let s = input;
  // Remove script tags and content
  s = s.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  // Remove any on* attributes (onerror, onclick, etc.)
  s = s.replace(/\s+on[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '');
  // Remove javascript: URIs
  s = s.replace(/javascript:\/\/[^\s"'>]*/gi, '');
  s = s.replace(/javascript:/gi, '');
  // Remove <iframe>, <img onerror=> patterns
  s = s.replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, '');
  s = s.replace(/<img\b[^>]*>/gi, (m) => m.replace(/on[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, ''));
  return s;
}

function escapeHtmlEntities(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// PII redaction
function redactPII(s) {
  let out = s;
  let redactions = { names: 0, ssn: 0, email: 0, phone: 0, address: 0 };

  // SSN
  out = out.replace(/\b\d{3}-\d{2}-\d{4}\b/g, () => { redactions.ssn++; return '[REDACTED SSN]'; });

  // Emails
  out = out.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, () => { redactions.email++; return '[REDACTED EMAIL]'; });

  // Phone numbers (various formats)
  out = out.replace(/\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b/g, () => { redactions.phone++; return '[REDACTED PHONE]'; });

  // Addresses (simple heuristic: number + street name + type)
  out = out.replace(/\b\d{1,6}\s+[A-Za-z0-9.\s]{2,60}\s(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b/gi, () => { redactions.address++; return '[REDACTED ADDRESS]'; });

  // Names: heuristic - two capitalized words (First Last) not at sentence end and not all-caps acronyms
  out = out.replace(/\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b/g, (m, p1, p2) => {
    // avoid redacting common sentence-start words like "The Store" by simple check: if contains 'Ltd' etc skip
    if (/\b(Street|St|Ave|Avenue|Mr|Mrs|Ms|Dr|Inc|LLC)\b/.test(m)) return m;
    redactions.names++;
    return '[REDACTED NAME]';
  });

  return { out, redactions };
}

function detectSqlInjection(s) {
  const patterns = /\b(select|drop|insert|delete|update|union|alter|create)\b|--|;\s*\b(or)\b/gi;
  return patterns.test(s);
}

function computeConfidence(original, sanitized, redactions) {
  // start at 0.95, penalize for heavy modifications
  let score = 0.95;
  const lengthRatio = sanitized.length / Math.max(1, original.length);
  if (lengthRatio < 0.5) score -= 0.2;
  const totalRedactions = Object.values(redactions).reduce((a,b)=>a+b,0);
  score -= Math.min(0.3, totalRedactions * 0.02);
  if (score < 0.1) score = 0.1;
  return Math.round(score * 100) / 100;
}

export default async function handler(req, res) {
  try {
    const ip = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown';
    if (!trackRate(ip)) {
      return res.status(429).json({ blocked: true, reason: 'rate limit exceeded', sanitizedOutput: '', confidence: 0.0 });
    }

    if (req.method !== 'POST') {
      return res.status(400).json({ blocked: true, reason: 'invalid method', sanitizedOutput: '', confidence: 0.0 });
    }

    const body = req.body;
    if (!body || typeof body !== 'object') {
      return res.status(400).json({ blocked: true, reason: 'invalid JSON body', sanitizedOutput: '', confidence: 0.0 });
    }

    const { userId, input, category } = body;
    if (!userId || typeof userId !== 'string' || !input || typeof input !== 'string' || category !== 'Output Sanitization') {
      return res.status(400).json({ blocked: true, reason: 'missing or invalid fields', sanitizedOutput: '', confidence: 0.0 });
    }

    // Step 1: Strip dangerous HTML/JS constructs
    const stripped = stripDangerousHtml(input);

    // Step 2: Detect SQL injection patterns
    if (detectSqlInjection(stripped)) {
      return res.status(200).json({ blocked: true, reason: 'SQL injection pattern detected', sanitizedOutput: '', confidence: 0.0 });
    }

    // Step 3: Redact PII
    const { out: redacted, redactions } = redactPII(stripped);

    // Step 4: Escape HTML entities for safe output
    const escaped = escapeHtmlEntities(redacted);

    const confidence = computeConfidence(input, escaped, redactions);

    const anyRedacted = Object.values(redactions).some(v => v > 0);
    const reasonParts = [];
    if (anyRedacted) reasonParts.push('PII redacted');
    if (escaped !== input) reasonParts.push('HTML/JS stripped and escaped');
    if (reasonParts.length === 0) reasonParts.push('no issues found');

    return res.status(200).json({ blocked: false, reason: reasonParts.join('; '), sanitizedOutput: escaped, confidence });
  } catch (err) {
    // Never leak internals
    return res.status(500).json({ blocked: true, reason: 'internal error', sanitizedOutput: '', confidence: 0.0 });
  }
}
