import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 20,             // 20 virtual users
  duration: '30s',     // last for 30 sec
};

export default function () {
  const url = 'http://localhost:8000/v1/jobs';
  const payload = JSON.stringify({ type: 'text.reverse', payload: { text: 'k6' } });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(url, payload, params);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(0.1);
}
