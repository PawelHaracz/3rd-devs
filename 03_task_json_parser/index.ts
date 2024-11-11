import { JsonProcessor } from './app';

const processor = new JsonProcessor();
processor.processJson().catch(console.error);
