#!/usr/bin/env python3
"""
开始新考试或恢复进行中的考试
POST /api/v1/exam/{exam_id}/questions 开始新考试
返回: attempt_id, questions[], started_at, duration_minutes, remaining_seconds
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="生成开始考试的 JS 代码")
    parser.add_argument("exam_id", type=int, help="考试ID")
    args = parser.parse_args()

    js = f"""
(async () => {{
  const token = localStorage.getItem('token');
  const examId = {args.exam_id};
  try {{
    const resp = await fetch(`/api/v1/exam/${{examId}}/questions`, {{
      method: 'POST',
      headers: {{ 'Authorization': `Bearer ${{token}}`, 'Content-Type': 'application/json' }}
    }});
    const data = await resp.json();
    if (!resp.ok) {{
      return JSON.stringify({{ error: true, status: resp.status, data }});
    }}
    return JSON.stringify({{
      attempt_id: data.attempt_id,
      questions_count: data.questions ? data.questions.length : 0,
      started_at: data.started_at,
      duration_minutes: data.duration_minutes,
      remaining_seconds: data.remaining_seconds,
      questions: data.questions
    }});
  }} catch (e) {{
    return JSON.stringify({{ error: true, message: e.message }});
  }}
}})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
