import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { VoiceGateway } from './voice/voice.gateway';

async function bootstrap() {
  // rawBody: true keeps the original request bytes so the webhook controller can
  // verify the YCloud signature against the exact payload that was signed.
  const app = await NestFactory.create(AppModule, { rawBody: true });

  // Security headers.
  app.use(helmet());

  // Everything lives under /api (the frontend talks to /api/...).
  app.setGlobalPrefix('api');

  // Allow the frontend origin. In dev the origin list comes from WEB_ORIGIN env
  // var; when that is not set (env file not found) we fall back to allowing all
  // origins — this tool is internal-only so wildcarding is safe.
  const allowedOrigins = process.env.WEB_ORIGIN
    ? process.env.WEB_ORIGIN.split(',').map((o) => o.trim())
    : null;
  app.enableCors({
    origin: allowedOrigins ?? ((_, cb) => cb(null, true)),
    credentials: false,
  });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: false,
    }),
  );

  const port = Number(process.env.API_PORT ?? 3001);
  await app.listen(port, '0.0.0.0');

  // Attach the ConversationRelay WebSocket to the HTTP server.
  // Must be after app.listen() so the underlying http.Server exists.
  const httpServer = app.getHttpServer();
  const voiceGateway = app.get(VoiceGateway);
  voiceGateway.attachToServer(httpServer);

  Logger.log(`API escuchando en http://localhost:${port}/api`, 'Bootstrap');
}

bootstrap();
