import type { Config } from '@netlify/functions';
import { getDatabase } from '@netlify/database';

const roles = [
  { id: 'backend-engineer', name: 'Backend Engineer', description: 'Reliable APIs, data systems, distributed services, and testing.' },
  { id: 'frontend-engineer', name: 'Frontend Engineer', description: 'Accessible interfaces, browser performance, state, and testing.' },
  { id: 'machine-learning-engineer', name: 'Machine Learning Engineer', description: 'Model development, evaluation, data pipelines, and production ML.' },
  { id: 'data-engineer', name: 'Data Engineer', description: 'Scalable pipelines, data modeling, quality, and analytics infrastructure.' },
];

const questionSets: Record<string, Array<[string, string, string]>> = {
  'backend-engineer': [
    ['API design', 'How would you design an idempotent API endpoint for a critical write operation?', 'medium'],
    ['Data modeling', 'Describe how you choose between normalization and denormalization.', 'medium'],
    ['Reliability', 'How would you diagnose and reduce intermittent latency in a distributed service?', 'hard'],
    ['Testing', 'What belongs in an effective integration test suite for an API?', 'medium'],
    ['Security', 'How do you protect a public API against common authentication and input attacks?', 'hard'],
  ],
  'frontend-engineer': [
    ['Accessibility', 'How do you make a complex interactive component accessible?', 'medium'],
    ['Performance', 'How would you investigate a slow page and improve its Core Web Vitals?', 'hard'],
    ['State', 'How do you decide where application state should live?', 'medium'],
    ['Testing', 'What is your strategy for testing a critical user flow?', 'medium'],
    ['Architecture', 'How would you structure a frontend that multiple teams can maintain?', 'hard'],
  ],
  'machine-learning-engineer': [
    ['Evaluation', 'How do you select metrics for an imbalanced classification problem?', 'medium'],
    ['Data', 'How would you detect and prevent data leakage?', 'hard'],
    ['Production ML', 'How do you monitor a deployed model for drift and degradation?', 'hard'],
    ['Experimentation', 'Describe how you make model experiments reproducible.', 'medium'],
    ['Systems', 'How would you design a low-latency inference service?', 'hard'],
  ],
  'data-engineer': [
    ['Pipelines', 'How would you design an idempotent batch data pipeline?', 'medium'],
    ['Modeling', 'When would you choose a star schema over a normalized model?', 'medium'],
    ['Quality', 'How do you detect and contain bad data before it reaches consumers?', 'hard'],
    ['Scale', 'How would you diagnose a distributed job that has become unexpectedly slow?', 'hard'],
    ['Operations', 'What observability does a production data platform need?', 'medium'],
  ],
};

type Question = { id: string; question: string; topic: string; difficulty: string; question_type: string };
type Answer = { question_id: string; answer: string; duration_seconds: number; evaluation: { score: number; feedback: string } };

const json = (body: unknown, status = 200) => Response.json(body, { status });
const detail = (message: string, status: number) => json({ detail: message }, status);
const digest = async (value: string) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))).map(byte => byte.toString(16).padStart(2, '0')).join('');

const makeQuestions = (role: string): Question[] => (questionSets[role] || questionSets['backend-engineer']).map(([topic, question, difficulty]) => ({
  id: crypto.randomUUID(), topic, question, difficulty, question_type: 'technical',
}));

const sessionView = (session: any) => {
  const questions = session.questions as Question[];
  const answers = session.answers as Answer[];
  return {
    session_id: session.id,
    role: session.role,
    status: session.status,
    total_questions: questions.length,
    answered_questions: answers.length,
    current_question: questions[answers.length] || null,
  };
};

const authorize = async (sessionId: string, req: Request) => {
  const db = getDatabase();
  const [session] = await db.sql`SELECT * FROM interview_sessions WHERE id = ${sessionId}::uuid`;
  if (!session) return { error: detail('Interview session not found', 404) };
  const token = req.headers.get('x-session-token') || '';
  if (!token || await digest(token) !== session.token_hash) return { error: detail('Valid session token required', 401) };
  return { session };
};

export default async (req: Request) => {
  try {
    const url = new URL(req.url);
    const path = url.pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean);
    const db = getDatabase();

    if (req.method === 'GET' && path[0] === 'roles' && path.length === 1) return json(roles);

    if (req.method === 'POST' && path[0] === 'resumes' && path.length === 1) {
      const form = await req.formData();
      const file = form.get('file');
      if (!(file instanceof File)) return detail('A resume file is required', 400);
      const suffix = file.name.toLowerCase().split('.').pop();
      if (!['pdf', 'txt'].includes(suffix || '')) return detail('Only PDF and text resumes are supported', 415);
      if (file.size > 5_000_000) return detail('Resume file is too large', 413);
      const bytes = new Uint8Array(await file.arrayBuffer());
      if (suffix === 'pdf' && new TextDecoder().decode(bytes.slice(0, 4)) !== '%PDF') return detail('The uploaded file is not a valid PDF', 422);
      const text = new TextDecoder('utf-8', { fatal: false }).decode(bytes).replace(/[^\x20-\x7E\n]/g, ' ').replace(/\s+/g, ' ').trim();
      const skillTerms = ['Python', 'Java', 'JavaScript', 'TypeScript', 'SQL', 'React', 'PostgreSQL', 'Docker', 'AWS', 'Machine Learning', 'TensorFlow', 'PyTorch', 'FastAPI'];
      const skills = skillTerms.filter(skill => text.toLowerCase().includes(skill.toLowerCase()));
      const resumeInfo = { skills, summary: skills.length ? `Experience includes ${skills.join(', ')}.` : 'Resume received and ready for role-based assessment.' };
      const id = crypto.randomUUID();
      await db.sql`INSERT INTO candidates (id, filename, resume_text, resume_info) VALUES (${id}::uuid, ${file.name}, ${text}, ${JSON.stringify(resumeInfo)}::jsonb)`;
      return json({ candidate_id: id, filename: file.name, resume_info: resumeInfo }, 201);
    }

    if (req.method === 'POST' && path[0] === 'sessions' && path.length === 1) {
      const body = await req.json() as { candidate_id?: string; role?: string };
      if (!body.candidate_id || !body.role || !roles.some(role => role.id === body.role)) return detail('A valid candidate and role are required', 400);
      const [candidate] = await db.sql`SELECT id FROM candidates WHERE id = ${body.candidate_id}::uuid`;
      if (!candidate) return detail('Candidate not found', 400);
      const id = crypto.randomUUID();
      const accessToken = `${crypto.randomUUID()}${crypto.randomUUID()}`;
      const questions = makeQuestions(body.role);
      await db.sql`INSERT INTO interview_sessions (id, candidate_id, role, token_hash, questions) VALUES (${id}::uuid, ${body.candidate_id}::uuid, ${body.role}, ${await digest(accessToken)}, ${JSON.stringify(questions)}::jsonb)`;
      return json({ session_id: id, role: body.role, status: 'active', total_questions: questions.length, answered_questions: 0, current_question: questions[0], access_token: accessToken }, 201);
    }

    if (path[0] === 'sessions' && path[1]) {
      const auth = await authorize(path[1], req);
      if (auth.error) return auth.error;
      const session: any = auth.session;

      if (req.method === 'POST' && path[2] === 'questions' && path[3] && path[4] === 'answers') {
        if (session.status !== 'active') return detail('Interview is already finished', 409);
        const questions = session.questions as Question[];
        const answers = session.answers as Answer[];
        const current = questions[answers.length];
        if (!current || current.id !== path[3]) return detail('This is not the current question', 400);
        const body = await req.json() as { answer?: string; duration_seconds?: number };
        if (!body.answer?.trim()) return detail('An answer is required', 400);
        const wordCount = body.answer.trim().split(/\s+/).length;
        const score = Math.max(3, Math.min(10, Math.round(3 + Math.min(wordCount, 100) / 15)));
        answers.push({ question_id: current.id, answer: body.answer.trim(), duration_seconds: body.duration_seconds || 0, evaluation: { score, feedback: score >= 7 ? 'Clear, detailed response with useful technical reasoning.' : 'Add a concrete example and discuss tradeoffs in more depth.' } });
        const status = answers.length === questions.length ? 'completed' : 'active';
        await db.sql`UPDATE interview_sessions SET answers = ${JSON.stringify(answers)}::jsonb, status = ${status} WHERE id = ${session.id}::uuid`;
        return json(sessionView({ ...session, answers, status }));
      }

      if (req.method === 'GET' && path[2] === 'results') {
        const questions = session.questions as Question[];
        const answers = session.answers as Answer[];
        if (session.status !== 'completed') return detail('Interview is not complete', 409);
        const scores = answers.map(item => item.evaluation.score);
        const overall = Number((scores.reduce((sum, score) => sum + score, 0) / scores.length).toFixed(1));
        return json({
          session_id: session.id,
          summary: `The interview was completed with an overall score of ${overall} out of 10.`,
          analysis: { overall_score: overall, strengths: overall >= 7 ? ['Technical communication', 'Structured reasoning'] : ['Completed the full interview'], areas_for_improvement: overall >= 7 ? ['Add more implementation detail'] : ['Use concrete examples', 'Discuss technical tradeoffs'] },
          questions: questions.map((question, index) => ({ ...question, answer: answers[index]?.answer || null, evaluation: answers[index]?.evaluation || null, retrieved_context: [] })),
        });
      }

      if (req.method === 'GET' && path.length === 2) return json(sessionView(session));
    }

    return detail('Not found', 404);
  } catch (error) {
    console.error('API request failed', error instanceof Error ? error.message : 'Unknown error');
    return detail('The interview service could not complete the request', 500);
  }
};

export const config: Config = { path: '/api/*' };
