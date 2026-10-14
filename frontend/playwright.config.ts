import {defineConfig,devices} from '@playwright/test';
export default defineConfig({
 testDir:'./tests',fullyParallel:false,workers:1,retries:0,
 reporter:[['list'],['html',{open:'never'}]],
 use:{baseURL:'http://localhost:3000',trace:'retain-on-failure',screenshot:'only-on-failure',...devices['Desktop Chrome'],viewport:{width:1440,height:1000}},
 webServer:{command:'npm run start',url:'http://localhost:3000/connexion',timeout:90000,reuseExistingServer:!process.env.CI}
});
