import discord
import asyncio
import os

from discord.ext import commands
from discord.ui import View, Button

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

MEM_ROLE_NAME = "MEM"
DEV_ROLE_NAME = "DEV"
CATEGORY_BUY = "Ticket Mua Hàng"
CATEGORY_SUPPORT = "Ticket Hỗ trợ/Bảo Hành"

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mua Hàng", style=discord.ButtonStyle.green, custom_id="buy")
    async def buy_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "mua-hang", CATEGORY_BUY)

    @discord.ui.button(label="Hỗ Trợ/Bảo Hành", style=discord.ButtonStyle.red, custom_id="support")
    async def support_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "ho-tro", CATEGORY_SUPPORT)

async def create_ticket(interaction: discord.Interaction, ticket_type: str, category_name: str):
    guild = interaction.guild
    member = interaction.user

    # Kiểm tra role MEM
    mem_role = discord.utils.get(guild.roles, name=MEM_ROLE_NAME)
    if mem_role not in member.roles:
        return await interaction.response.send_message("Bạn không có quyền mở ticket.", ephemeral=True)

    # Kiểm tra xem đã có ticket chưa
    for channel in guild.text_channels:
        if (channel.name.startswith("mua-hang") or channel.name.startswith("ho-tro")) and channel.topic == f"user:{member.id}":
            return await interaction.response.send_message("Bạn đã có một ticket đang mở.", ephemeral=True)

    # Tạo category nếu chưa có
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)

    # Tạo permission cho channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    dev_role = discord.utils.get(guild.roles, name=DEV_ROLE_NAME)
    if dev_role:
        overwrites[dev_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # Tạo ticket channel và đánh dấu topic để dễ kiểm tra
    ticket_channel = await guild.create_text_channel(
        name=f"🎟┃{ticket_type}-{member.name}",
        category=category,
        overwrites=overwrites,
        topic=f"user:{member.id}"
    )

    await ticket_channel.send(
        f"{member.mention} đã mở ticket `{ticket_type.replace('-', ' ').title()}`. <@&1368845823764336681> sẽ hỗ trợ bạn."
    )

    embed = discord.Embed(
    title="Vui Lòng Chờ DEV Xíu Nhé.\nDEV Sẽ Trả Lời Nhanh Nhất Có Thể Ạ",
    color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=6820daa8&is=681f8928&hm=b64bb634019a3f01aa99fd7bc00e00f53d7e1e7ace795815357feaa3612e17c5&")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1351234840749670430/1370931335312707604/standard_77.gif?ex=68214acd&is=681ff94d&hm=cc7c1da012d917ae93c5037b6615a45ce18bd44b29d968e626ca6c659b150629&")  # đổi link ảnh tùy bạn

    await ticket_channel.send(embed=embed, view=CloseTicketView())


    await interaction.response.send_message(f"Ticket của bạn đã được tạo: {ticket_channel.mention}", ephemeral=True)


class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # ❌ XÓA DÒNG NÀY VÌ ĐÃ TẠO BUTTON BẰNG DECORATOR Ở DƯỚI
        # self.add_item(Button(label="Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket"))

    @discord.ui.button(label="Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        dev_role = discord.utils.get(interaction.guild.roles, name=DEV_ROLE_NAME)
        if dev_role not in interaction.user.roles:
            return await interaction.response.send_message("Bạn không có quyền đóng ticket này.", ephemeral=True)

        await interaction.response.send_message("Ticket sẽ bị đóng sau 5 giây...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def sendticket(ctx):
    embed = discord.Embed(
        title="Ticket Hỗ Trợ",
        description="Nếu bạn cần mua hàng hoặc hỗ trợ, hãy bấm vào các nút bên dưới.\n**VUI LÒNG KHÔNG SPAM TICKET**",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=6820daa8&is=681f8928&hm=b64bb634019a3f01aa99fd7bc00e00f53d7e1e7ace795815357feaa3612e17c5&")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1351234840749670430/1370931335312707604/standard_77.gif?ex=68214acd&is=681ff94d&hm=cc7c1da012d917ae93c5037b6615a45ce18bd44b29d968e626ca6c659b150629&")  # đổi link ảnh tùy bạn

    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete(delay=5)

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def close(ctx):
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        await ctx.send("Đóng ticket...")
        await ctx.channel.delete()
    else:
        await ctx.send("Lệnh này chỉ dùng trong ticket.")


@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def thanhtoan(ctx, sotien: int, *, loi_nhan: str):
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        bank_code = "VCB"
        account_no = "1034298524"
        account_name = "MAI LIEM TRUC"
        loi_nhan_encoded = loi_nhan.replace(" ", "+")
        account_name_encoded = account_name.replace(" ", "+")

        qr_url = (
            f"https://img.vietqr.io/image/{bank_code}-{account_no}-compact2.png"
            f"?amount={sotien}&addInfo={loi_nhan_encoded}&accountName={account_name_encoded}"
        )

        # Dạng mô phỏng khung input đẹp mắt
        info_block = (
            f"```ini\n"
            f"Ngân hàng:\nVietcombank\n\n"
            f"Số Tài Khoản:\n{account_no}\n\n"
            f"Chủ Tài Khoản:\n{account_name}\n\n"
            f"Số Tiền:\n{sotien:,} VND\n\n"
            f"Nội dung chuyển:\n{loi_nhan}\n\n"
            f"Ghi chú:\nKhách hàng vui lòng gửi bill vào ticket.\n"
            f"```"
        )

        embed = discord.Embed(
            title="Thông Tin Thanh Toán",
            description=info_block,
            color=discord.Color.green()
        )

        embed.set_image(url=qr_url)
        embed.set_footer(text="Mọi thắc mắc liên hệ OW.")

        await ctx.send(embed=embed)
    else:
        await ctx.send("Lệnh này chỉ dùng trong kênh ticket.")


@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def banggia(ctx):
    channel = discord.utils.get(ctx.guild.text_channels, name="📰│bảng-giá")
    if channel is None:
        await ctx.send("Không tìm thấy kênh 📰│bảng-giá.")
        return

    embed = discord.Embed(
        title="OW STORE",
        description="**BẢNG GIÁ OW STORE**",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Dịch vụ Auto Fram",
        value=(
            "• Key │Price : 10k/ngày, 60k/tuần, 100k/tháng, 300k/vv\n"
            "• Key vĩnh viễn và dùng được tất cả các loại tool mà OW STORE hiện có │Price : 1tr2\n"
            "• Viết Auto theo yêu cầu\n"
            "• Mở 🎫│ticket để biết thêm chi tiết về Auto Fram"
        ),
        inline=False
    )

    embed.add_field(
        name="Dịch vụ cày thuê LV GTA5VN",
        value=(
            "• Theo yêu cầu\n"
            "• SV2 từ LV0 -> LV25 │Price : 90k"
        ),
        inline=False
    )

    embed.add_field(
        name="Dịch vụ thiết kế đồ họa",
        value="• Vẽ Logo, Banner, Poster, Social Post theo nhu cầu",
        inline=False
    )

    embed.add_field(
        name="Dịch vụ thiết kế discord",
        value="• Thiết kế server discord theo yêu cầu (ví dụ: discord Gang, Store, Setup Bot theo yêu cầu...) │Price: 50k",
        inline=False
    )

    embed.add_field(
        name="Dịch vụ làm Excel, Word, PowerPoint, Canva",
        value=(
            "• PowerPoint, Canva │Price: 8k/slide (càng nhiều giá càng tốt)\n"
            "• Word: Tùy theo yêu cầu\n"
            "• Excel: Tùy theo yêu cầu"
        ),
        inline=False
    )

    embed.add_field(
        name="Dịch vụ cài các phần mềm của ADOBE và MICROSOFT",
        value=(
            "• Combot Adobe Illustrator và Adobe Photoshop │Price : 150k\n"
            "• Trọn bộ Microsoft Office │Price : 150k"
        ),
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=6820daa8&is=681f8928&hm=b64bb634019a3f01aa99fd7bc00e00f53d7e1e7ace795815357feaa3612e17c5&")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1351234840749670430/1370931335312707604/standard_77.gif?ex=68214acd&is=681ff94d&hm=cc7c1da012d917ae93c5037b6615a45ce18bd44b29d968e626ca6c659b150629&")  # đổi link ảnh tùy bạn

    await channel.send(embed=embed)
    await ctx.message.delete(delay=5)


@bot.event
async def on_member_join(member):
    # Tìm kênh chào mừng theo tên
    channel = discord.utils.get(member.guild.text_channels, name="🎉│chào-mừng")
    if channel is None:
        return

    # Thay ID bên dưới bằng ID thật của từng kênh
    update_channel_id = 1370973547236692018  # 🚨│update
    rule_channel_id = 1370973612286279792   # 📖│luật-dịch-vụ
    ticket_channel_id = 1352312400686354553 # 🎫│ticket
    price_channel_id = 1370966758495879206  # 📰│bảng-giá (ID giả, thay bằng ID thật)

    embed = discord.Embed(
        description=f"Chào mừng {member.mention} đã đến với **OW STORE**. Chúng tôi hy vọng bạn sẽ hài lòng khi đến với store của chúng tôi.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="\u200b",
        value=f"• Hãy xem kênh <#{update_channel_id}> để nhận thông báo mỗi khi chúng tôi có thay đổi hoặc sự kiện hấp dẫn.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là luật khi sử dụng dịch vụ tại store của chúng tôi <#{rule_channel_id}>.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là nơi để bạn mua hàng hoặc cần chúng tôi hỗ trợ bảo hành <#{ticket_channel_id}>.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là bảng giá dịch vụ tại store của chúng tôi <#{price_channel_id}>.",
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=6820daa8&is=681f8928&hm=b64bb634019a3f01aa99fd7bc00e00f53d7e1e7ace795815357feaa3612e17c5&")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1351234840749670430/1370931335312707604/standard_77.gif?ex=68214acd&is=681ff94d&hm=cc7c1da012d917ae93c5037b6615a45ce18bd44b29d968e626ca6c659b150629&")  # đổi link ảnh tùy bạn

    await channel.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Bạn không có quyền để dùng lệnh này.")


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f'Bot is ready: {bot.user}')

bot.run(os.getenv("DISCORD_TOKEN"))
