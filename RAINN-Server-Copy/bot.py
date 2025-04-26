import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from datetime import datetime, timezone

# Bot Ayarları
TOKEN = 'BOT TOKENİNİZ'
SOURCE_GUILD_ID = 1234567342389  # Şablon Alınacak Sunucu Id  
TARGET_GUILD_ID = 1234567342389   # Şablon Yapıştırılacak Sunucu Id
LOG_CHANNEL_ID = 1234567342389  # Logların Gönderileceği Kanal Id 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.template = None

async def send_log(message, author=None):
    """Log Mesajını Belirlenen Kanala Gönderir"""
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Şablon Log",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if author:
                embed.add_field(name="Kullanıcı", value=author.mention, inline=True)
            
            embed.add_field(name="Açıklama", value=message, inline=False)
            embed.set_footer(text="Developed By RAINN")
            await channel.send(embed=embed)
    except Exception as e:
        print(f"Log Gönderilemedi: {e}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} Aktif!')
    await bot.change_presence(
        activity=discord.Streaming(
            name="discord.gg/neonleak",
            url="https://twitch.tv/rainnxa"
        ),
        status=discord.Status.do_not_disturb
    )
    print(f'Komutlar: !kopyala ve !yapistir')
    await send_log(f"Bot Aktif: {bot.user.name}")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
@commands.has_permissions(administrator=True)
async def kopyala(ctx):
    """Sunucu Şablonunu Kopyalar"""
    guild = bot.get_guild(SOURCE_GUILD_ID)
    if not guild:
        await send_log("❌ Kaynak Sunucu Bulunamadı!")
        return await ctx.send("Kaynak Sunucu Bulunamadı!")
    
    await ctx.send("Şablon Oluşturuluyor...")
    await send_log(f"🔧 {ctx.author.mention} Tarafından Şablon Oluşturma Başlatıldı (Sunucu: {guild.name})")
    
    try:
        bot.template = await create_template(guild)
        log_msg = f"✅ Şablon Oluşturuldu:\n- {len(bot.template['roles'])} Rol\n- {len(bot.template['channels'])} Kanal"
        await send_log(log_msg)
        await ctx.send("Şablon Oluşturuldu! `!yapistir` Komutu İle Uygulayabilirsiniz.")
    except Exception as e:
        error_msg = f"❌ Şablon Oluşturma Hatası: {str(e)}"
        await send_log(error_msg)
        await ctx.send(f"Hata Oluştu: {str(e)}")

@bot.command()
@commands.has_permissions(administrator=True)
async def yapistir(ctx):
    """Şablonu Uygular"""
    if not bot.template:
        await send_log("❌ Şablon Uygulama Hatası: Önce Şablon Oluşturulmalı")
        return await ctx.send("Önce Bir Şablon Oluşturun! (`!kopyala`)")
    
    guild = bot.get_guild(TARGET_GUILD_ID)
    if not guild:
        await send_log("❌ Hedef Sunucu Bulunamadı")
        return await ctx.send("Hedef Sunucu Bulunamadı!")
    
    await ctx.send("Şablon Uygulanıyor...")
    await send_log(f"🔨 {ctx.author.mention} Tarafından Şablon Uygulama Başlatıldı! (Sunucu: {guild.name})")
    
    try:
        start_time = datetime.now()
        await apply_template(guild, bot.template)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_msg = (
            f"✅ Şablon Başarıyla Uygulandı!\n"
            f"- Sunucu: {guild.name}\n"
            f"- Süre: {duration:.2f} Saniye\n"
            f"- {len(bot.template['roles'])} Rol Oluşturuldu!\n"
            f"- {len(bot.template['channels'])} Kanal Oluşturuldu!"
        )
        await send_log(log_msg)
        await ctx.send("✅ Şablon Başarıyla Uygulandı!")
    except Exception as e:
        error_msg = f"❌ Şablon Uygulama Hatası: {str(e)}"
        await send_log(error_msg)
        await ctx.send(f"Hata Oluştu: {str(e)}")

async def create_template(guild):
    """Şablon Oluşturma Fonksiyonu"""
    template = {
    'roles': [],
    'channels': [],
    'created_at': datetime.now(timezone.utc).isoformat(),
    'source_guild': guild.name
}
    
    # Rolleri Kopyala
    for role in guild.roles:
        if role.name != '@everyone':
            template['roles'].append({
                'name': role.name,
                'permissions': role.permissions.value,
                'color': role.color.value,
                'hoist': role.hoist,
                'mentionable': role.mentionable
            })
    
    # Kanalları Kopyala
    for channel in guild.channels:
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
            channel_data = {
                'name': channel.name,
                'type': str(channel.type),
                'position': channel.position,
                'category': channel.category.name if channel.category else None,
                'overwrites': []
            }
            
            # İzinleri Kopyala
            for target, overwrite in channel.overwrites.items():
                allow, deny = overwrite.pair()
                channel_data['overwrites'].append({
                    'target': target.name,
                    'target_type': 'role' if isinstance(target, discord.Role) else 'member',
                    'allow': allow.value,
                    'deny': deny.value
                })
            
            template['channels'].append(channel_data)
    
    return template

async def apply_template(guild, template):
    """Şablon Uygulama Fonksiyonu"""
    created_roles = 0
    created_channels = 0
    
    # Rolleri Oluştur
    role_mapping = {}
    for role_data in template['roles']:
        try:
            role = await guild.create_role(
                name=role_data['name'],
                permissions=discord.Permissions(role_data['permissions']),
                color=discord.Color(role_data['color']),
                hoist=role_data['hoist'],
                mentionable=role_data['mentionable']
            )
            role_mapping[role_data['name']] = role
            created_roles += 1
            await asyncio.sleep(1)
        except Exception as e:
            await send_log(f"⚠️ Rol Oluşturulamadı: {role_data['name']} - {str(e)}")
    
    # Kanalları Oluştur
    category_mapping = {}
    for channel_data in template['channels']:
        try:
            if channel_data['type'] == 'category':
                category = await guild.create_category(
                    name=channel_data['name'],
                    position=channel_data['position']
                )
                category_mapping[channel_data['name']] = category
                created_channels += 1
            else:
                category = category_mapping.get(channel_data['category']) if channel_data['category'] else None
                
                if channel_data['type'] == 'text':
                    channel = await guild.create_text_channel(
                        name=channel_data['name'],
                        position=channel_data['position'],
                        category=category
                    )
                    created_channels += 1
                elif channel_data['type'] == 'voice':
                    channel = await guild.create_voice_channel(
                        name=channel_data['name'],
                        position=channel_data['position'],
                        category=category
                    )
                    created_channels += 1
                
                # İzinleri Uygula
                for overwrite_data in channel_data['overwrites']:
                    try:
                        if overwrite_data['target_type'] == 'role':
                            target = discord.utils.get(guild.roles, name=overwrite_data['target'])
                        else:
                            target = discord.utils.get(guild.members, name=overwrite_data['target'])
                        
                        if target:
                            await channel.set_permissions(
                                target,
                                overwrite=discord.PermissionOverwrite.from_pair(
                                    discord.Permissions(overwrite_data['allow']),
                                    discord.Permissions(overwrite_data['deny'])
                                )
                            )
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        await send_log(f"⚠️ İzin Uygulanamadı: {overwrite_data['target']} - {str(e)}")
            
            await asyncio.sleep(1)
        except Exception as e:
            await send_log(f"⚠️ Kanal Oluşturulamadı: {channel_data['name']} - {str(e)}")
    
    return created_roles, created_channels

bot.run(TOKEN)