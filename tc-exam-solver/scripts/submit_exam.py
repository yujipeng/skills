#!/usr/bin/env python3
"""
提交考试答案
POST /api/v1/exam/{exam_id}/submit?attempt_id={attempt_id}
payload: {"answers": [{"question_id": N, "answer": "A/B/C/D"}], "auto_submit": false}
返回: attempt_id, score, total_possible, passed, pass_threshold
"""
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="生成提交考试答案的 JS 代码")
    parser.add_argument("exam_id", type=int, help="考试ID")
    parser.add_argument("attempt_id", type=int, help="考试尝试ID")
    parser.add_argument("answers_json", type=str, help='答案JSON字符串，格式: [{"question_id":N,"answer":"A"}]')
    args = parser.parse_args()

    # 验证 answers_json 格式
    try:
        answers = json.loads(args.answers_json)
        answers_str = json.dumps(answers)
    except json.JSONDecodeError as e:
        print(f"answers_json 格式错误: {e}")
        raise SystemExit(1)

    js = f"""
(async () => {{
  const token = localStorage.getItem('token');
  const examId = {args.exam_id};
  const attemptId = {args.attempt_id};
  const answers = {answers_str};
  try {{
    const resp = await fetch(`/api/v1/exam/${{examId}}/submit?attempt_id=${{attemptId}}`, {{
      method: 'POST',
      headers: {{ 'Authorization': `Bearer ${{token}}`, 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ answers, auto_submit: false }})
    }});
    const data = await resp.json();
    if (!resp.ok) {{
      return JSON.stringify({{ error: true, status: resp.status, data }});
    }}
    return JSON.stringify({{
      attempt_id: data.attempt_id,
      score: data.score,
      total_possible: data.total_possible,
      passed: data.passed,
      pass_threshold: data.pass_threshold
    }});
  }} catch (e) {{
    return JSON.stringify({{ error: true, message: e.message }});
  }}
}})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
