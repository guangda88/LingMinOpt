"""
Inbox command for lingminopt CLI — LingMessage integration.
"""

import asyncio

import click


def _inbox_read(db_url: str, agent_id: str, show_threads: bool, unread_only: bool) -> None:
    """Read inbox messages from LingMessage PostgreSQL database."""
    async def _read():
        import asyncpg

        conn = await asyncpg.connect(db_url)
        try:
            if show_threads:
                rows = await conn.fetch(
                    "SELECT t.id, t.topic, t.status, t.priority, t.current_round, "
                    "  (SELECT COUNT(*) FROM lingmessage_messages m WHERE m.thread_id = t.id) as msg_count "
                    "FROM lingmessage_threads t "
                    "WHERE t.status = 'active' "
                    "ORDER BY t.priority = 'high' DESC, t.created_at DESC "
                    "LIMIT 20"
                )
                if not rows:
                    click.echo("📭 没有活跃的议事厅线程")
                    return
                click.echo(f"\n📋 议事厅线程 (共{len(rows)}个)")
                click.echo("=" * 70)
                for r in rows:
                    flag = "🔴" if r["priority"] == "high" else "🟢"
                    click.echo(f"  {flag} #{r['id']} [{r['status']}] {r['topic']} ({r['msg_count']}条消息)")

            rows = await conn.fetch(
                "SELECT m.id, m.thread_id, t.topic, a.display_name, "
                "  LEFT(m.content, 200) as preview, m.message_type, m.created_at "
                "FROM lingmessage_messages m "
                "JOIN lingmessage_threads t ON t.id = m.thread_id "
                "JOIN lingmessage_agents a ON a.agent_id = m.agent_id "
                "WHERE m.agent_id != $1 "
                "ORDER BY m.created_at DESC LIMIT 10",
                agent_id
            )
            if rows:
                click.echo(f"\n📬 最新消息 (共{len(rows)}条)")
                click.echo("=" * 70)
                for r in rows:
                    msg_type = r["message_type"]
                    tag = "📌" if msg_type == "task_assignment" else ("🔔" if msg_type == "direct_mention" else "💬")
                    preview = (r["preview"] or "")[:60]
                    click.echo(f"  {tag} [线程#{r['thread_id']}] {r['display_name']} → {preview}...")
                    click.echo(f"     ({r['created_at']})  回复: lingminopt inbox --reply {r['thread_id']} --message '你的回复'")
        finally:
            await conn.close()

    asyncio.run(_read())


def _inbox_reply(db_url: str, agent_id: str, thread_id: str, content: str) -> None:
    """Reply to a LingMessage thread via PostgreSQL."""
    async def _reply():
        import asyncpg

        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "INSERT INTO lingmessage_messages (thread_id, agent_id, round_number, content, message_type) "
                "SELECT $1::integer, $2, "
                "  COALESCE(MAX(round_number), 0) + 1, $3, 'response' "
                "FROM lingmessage_messages WHERE thread_id = $1::integer",
                int(thread_id), agent_id, content
            )
            click.echo(f"✅ 回复已发送到线程 #{thread_id}")
        finally:
            await conn.close()

    try:
        asyncio.run(_reply())
    except Exception as e:
        click.echo(f"❌ 发送失败: {e}")
