import url from 'url';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const apiPath = path.join(__dirname, '..', 'pages', 'api', 'sanitize.js');

const mod = await import(url.pathToFileURL(apiPath));
const handler = mod.default;

function makeReq(body) {
  return {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
    socket: { remoteAddress: '127.0.0.1' }
  };
}

function makeRes() {
  let statusCode = 200;
  let jsonBody;
  return {
    status(code) { statusCode = code; return this; },
    json(obj) { jsonBody = obj; return Promise.resolve({ statusCode, body: obj }); },
  };
}

async function runTest(input) {
  const req = makeReq(input);
  req.body = input;
  const res = makeRes();
  const result = await handler(req, res);
  if (result && result.body) return result;
  return { statusCode: 200, body: null };
}

async function main() {
  const tests = [
    {
      name: 'PII exposure test',
      body: { userId: 'user-1', input: 'John Smith, SSN: 123-45-6789, lives at 123 Main St', category: 'Output Sanitization' }
    },
    {
      name: 'XSS attempt',
      body: { userId: 'user-2', input: '<script>alert(1)</script><img src=x onerror=alert(2)>Hello', category: 'Output Sanitization' }
    },
    {
      name: 'SQL injection',
      body: { userId: 'user-3', input: "Robert'); DROP TABLE Students;--", category: 'Output Sanitization' }
    }
  ];

  for (const t of tests) {
    try {
      const out = await runTest(t.body);
      console.log('---', t.name, '---');
      console.log('HTTP status:', out.statusCode);
      console.log('Body:', JSON.stringify(out.body, null, 2));
    } catch (err) {
      console.error('Test failed', t.name, err.message);
    }
  }
}

main();
