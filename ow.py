import discord
import asyncio
import os
import random
import re
from discord.ext import commands
from datetime import datetime, timedelta
from discord.ui import View, Button
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

MEM_ROLE_NAME = "MEM"
DEV_ROLE_NAME = "DEV"
CATEGORY_BUY = "Ticket Mua Hàng"
CATEGORY_SUPPORT = "Ticket Hỗ trợ/Bảo Hành"

# Lưu giveaway đang hoạt động hoặc có thể reroll
giveaway_views = {}

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
        f"{member.mention} đã mở ticket `{ticket_type.replace('-', ' ').title()}`. <@&1351227654782714040> sẽ hỗ trợ bạn."
    )

    embed = discord.Embed(
    title="Vui Lòng Chờ DEV Xíu Nhé.\nDEV Sẽ Trả Lời Nhanh Nhất Có Thể Ạ",
    color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

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
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

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
    await ctx.message.delete(delay=5)  # Xóa lệnh người dùng sau 5 giây
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        bank_code = "VCB"
        account_no = "1034298524"
        account_name = "MAI LIEM TRUC"
        loi_nhan_encoded = loi_nhan.replace(" ", "+")
        account_name_encoded = account_name.replace(" ", "+")

        qr_url = (
            f"https://img.vietqr.io/image/{bank_code}-{account_no}-compact.png"
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
            "• Key │Price : 15k/ngày, 90k/tuần, 160k/tháng, 300k/vv\n"
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
        value=(
            "• Thiết kế server discord theo yêu cầu (ví dụ: discord Gang, Store, Setup Bot theo yêu cầu...) │Price: 50k\n"
            "• Code bot discord theo yêu cầu (bot ticket, tạo mã qr, check người chơi của các server,....) │Price: 100k-500k"
        ),
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

    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

    await channel.send(embed=embed)
    await ctx.message.delete(delay=5)


@bot.event
async def on_member_join(member):
    # Tìm kênh chào mừng theo tên
    channel = discord.utils.get(member.guild.text_channels, name="🎉│chào-mừng")
    if channel is None:
        return

    # Thay ID bên dưới bằng ID thật của từng kênh
    update_channel_id = 1351223923966083152  # 🚨│update
    rule_channel_id = 1351226270414934091   # 📖│luật-dịch-vụ
    ticket_channel_id = 1351232807908675614 # 🎫│ticket
    price_channel_id = 1351224397427642490  # 📰│bảng-giá (ID giả, thay bằng ID thật)

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

    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

    await channel.send(embed=embed)

#------------------------------------------------------------------------------------------------------------
class GiveawayView(View):
    def __init__(self, giveaway_message, end_callback=None):
        super().__init__(timeout=None)
        self.participants = set()
        self.giveaway_message = giveaway_message
        self.end_callback = end_callback

    @discord.ui.button(label="Tham gia Giveaway", style=discord.ButtonStyle.green, custom_id="giveaway_join")
    async def join_button(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        if user.id in self.participants:
            await interaction.response.send_message("Bạn đã tham gia rồi!", ephemeral=True)
        else:
            self.participants.add(user.id)
            await interaction.response.send_message("Bạn đã tham gia giveaway!", ephemeral=True)
            await self.update_embed()

    async def update_embed(self):
        embed = self.giveaway_message.embeds[0]
        lines = embed.description.splitlines()

        # Loại bỏ dòng cũ nếu đã có
        lines = [line for line in lines if not line.startswith("👥 Số người tham gia:")]

        # Thêm dòng mới hiển thị số người tham gia
        lines.insert(2, f"👥 Số người tham gia: **{len(self.participants)}**")

        embed.description = "\n".join(lines)
        await self.giveaway_message.edit(embed=embed, view=self)

    async def end_giveaway(self):
        if self.participants:
            participants = list(self.participants)
            while participants:
                winner_id = random.choice(participants)
                winner = self.giveaway_message.guild.get_member(winner_id)
                if winner:
                    # Gửi tin nhắn chúc mừng
                    try:
                        prize = self.giveaway_message.embeds[0].description.splitlines()[0].split("**")[1]
                    except Exception:
                        prize = "phần thưởng"
                    try:
                        await winner.send(
                            f"🎉 Chúc mừng bạn đã thắng giveaway: **{prize}** 🎉"
                        )
                    except discord.Forbidden:
                        pass

                    await self.giveaway_message.channel.send(f"🎉 Giveaway kết thúc! Người thắng là {winner.mention} 🎉")
                    # Xóa giveaway khỏi bộ nhớ vì đã có người thắng hợp lệ
                    giveaway_views.pop(self.giveaway_message.id, None)
                    self.clear_items()
                    await self.giveaway_message.edit(view=None)
                    return
                else:
                    participants.remove(winner_id)

            # Không tìm được người thắng hợp lệ (tất cả người tham gia không còn trong server)
            await self.giveaway_message.channel.send(
                f"🎉 Giveaway kết thúc nhưng không thể xác định người thắng (không ai còn trong server).\n"
                f"👉 Bạn có thể dùng lệnh `!reroll {self.giveaway_message.id}` để quay lại từ danh sách ban đầu."
            )
            # **Giữ giveaway trong giveaway_views để reroll được**
            self.clear_items()
            await self.giveaway_message.edit(view=None)
        else:
            # Không có người tham gia
            await self.giveaway_message.channel.send("Giveaway kết thúc nhưng không có người tham gia nào.")
            giveaway_views.pop(self.giveaway_message.id, None)
            self.clear_items()
            await self.giveaway_message.edit(view=None)


def parse_time_string(time_str: str) -> int:
    time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    match = re.fullmatch(r"(\d+)([dhms])", time_str.lower())
    if not match:
        raise commands.BadArgument("Định dạng thời gian không hợp lệ. Dùng ví dụ: `1d`, `2h`, `30m`, `45s`")
    value, unit = match.groups()
    return int(value) * time_units[unit]

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def giveaway(ctx, time_str: str, *, prize: str):
    await ctx.message.delete(delay=5)

    try:
        time_in_seconds = parse_time_string(time_str)
    except commands.BadArgument as e:
        return await ctx.send(str(e))

    end_time = datetime.utcnow() + timedelta(seconds=time_in_seconds)
    end_timestamp = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 Giveaway Đã Bắt Đầu! 🎉",
        description=f"Phần thưởng: **{prize}**\n"
                    f"Kết thúc vào: <t:{end_timestamp}:F> (<t:{end_timestamp}:R>)\n"
                    "👥 Số người tham gia: **0**\n\n"
                    "Nhấn nút bên dưới để tham gia giveaway!",
        color=discord.Color.gold()
    )

    giveaway_message = await ctx.send(embed=embed, view=None)
    view = GiveawayView(giveaway_message)
    giveaway_views[giveaway_message.id] = view
    await giveaway_message.edit(view=view)

    await asyncio.sleep(time_in_seconds)
    await view.end_giveaway()

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def reroll(ctx, message_id: int):
    view = giveaway_views.get(message_id)
    if not view:
        return await ctx.send("Không tìm thấy giveaway tương ứng hoặc đã kết thúc.")

    participants = list(view.participants)
    if not participants:
        return await ctx.send("Không có người tham gia trong giveaway này.")

    while participants:
        winner_id = random.choice(participants)
        winner = ctx.guild.get_member(winner_id)
        if winner:
            await ctx.send(f"Quay lại: Người thắng mới là {winner.mention} 🎉")
            try:
                await winner.send("Bạn đã được chọn lại là người thắng giveaway!")
            except discord.Forbidden:
                pass
            return
        else:
            participants.remove(winner_id)

    await ctx.send("Không thể tìm thấy người nào còn trong server để chọn lại.")
#------------------------------------------------------------------------------------------------------------


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Bạn không có quyền để dùng lệnh này.")

@bot.event
async def on_ready():
    # Thêm view tùy chỉnh
    bot.add_view(TicketView())

    # Cập nhật trạng thái bot
    activity = discord.Activity(type=discord.ActivityType.watching, name="OW STORE -  Đa dịch vụ, giá hợp lý, hỗ trợ tận tâm 🔥")
    await bot.change_presence(activity=activity)

    print(f'Bot is ready: {bot.user}')




app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
