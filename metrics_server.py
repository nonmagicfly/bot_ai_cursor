"""
HTTP сервер для предоставления метрик Prometheus
"""
import asyncio
from aiohttp import web
from metrics import get_metrics, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)


async def metrics_handler(request):
    """Обработчик запросов метрик"""
    try:
        metrics_data = get_metrics()
        # Убираем charset из content_type для совместимости с aiohttp
        content_type = CONTENT_TYPE_LATEST.split(';')[0] if ';' in CONTENT_TYPE_LATEST else CONTENT_TYPE_LATEST
        return web.Response(
            text=metrics_data.decode('utf-8'),
            content_type=content_type,
            charset='utf-8'
        )
    except Exception as e:
        logger.error(f"Ошибка при получении метрик: {e}")
        # Убираем charset из content_type для совместимости с aiohttp
        content_type = CONTENT_TYPE_LATEST.split(';')[0] if ';' in CONTENT_TYPE_LATEST else CONTENT_TYPE_LATEST
        return web.Response(
            text=f"# Ошибка получения метрик: {e}\n",
            status=500,
            content_type=content_type,
            charset='utf-8'
        )


async def health_handler(request):
    """Health check endpoint"""
    return web.Response(text="OK", status=200)


def create_app():
    """Создание приложения aiohttp"""
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    app.router.add_get('/health', health_handler)
    return app


async def run_metrics_server(port=8000):
    """Запуск HTTP сервера для метрик"""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Метрики Prometheus доступны на http://0.0.0.0:{port}/metrics")
    return runner


if __name__ == '__main__':
    async def main():
        runner = await run_metrics_server(8000)
        try:
            await asyncio.Event().wait()  # Бесконечное ожидание
        except KeyboardInterrupt:
            logger.info("Остановка сервера метрик...")
        finally:
            await runner.cleanup()
    
    asyncio.run(main())


