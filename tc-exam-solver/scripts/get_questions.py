#!/usr/bin/env python3
"""
获取当前考试的题目和选项（含已作答状态）
GET /api/v1/exam/{exam_id}/progress?attempt_id={attempt_id}
返回完整题目列表 + 当前已保存的答案
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="生成获取考试题目的 JS 代码")
    parser.add_argument("exam_id", type=int, help="考试ID")
    parser.add_argument("attempt_id", type=int, help="考试尝试ID")
    args = parser.parse_args()

    js = f"""
(async () => {{
  const token = localStorage.getItem('token');
  const examId = {args.exam_id};
  const attemptId = {args.attempt_id};
  try {{
    const resp = await fetch(`/api/v1/exam/${{examId}}/progress?attempt_id=${{attemptId}}`, {{
      headers: {{ 'Authorization': `Bearer ${{token}}`, 'Content-Type': 'application/json' }}
    }});
    if (!resp.ok) {{
      const errData = await resp.json().catch(() => ({{}}));
      return JSON.stringify({{ error: true, status: resp.status, data: errData }});
    }}
    const data = await resp.json();
    // 完整返回题目+选项+已保存的答案
    return JSON.stringify({{
      attempt_id: data.attempt_id,
      questions: data.questions,
      answers: data.answers || [],
      remaining_seconds: data.remaining_seconds,
      duration_minutes: data.duration_minutes
    }});
  }} catch (e) {{
    return JSON.stringify({{ error: true, message: e.message }});
  }}
}})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
