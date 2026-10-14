import {test,expect,type Page} from '@playwright/test';
const password=process.env.E2E_PASSWORD;
if(!password)throw new Error('Set E2E_PASSWORD for disposable browser fixtures');
async function login(page:Page,name:string){
 await page.goto('/connexion');
 await page.getByLabel('Adresse e-mail').fill(name+'@test.invalid');
 await page.getByLabel('Mot de passe').fill(password!);
 await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await expect(page).toHaveURL(new RegExp(name==='client'?'/portail/dossiers/atlas/overview$':'/cabinet$'));
}
test('Les dossiers sont protégés avant authentification',async({page})=>{
 await page.goto('/cabinet/dossiers/atlas/overview');await expect(page).toHaveURL(/\/connexion$/);
 await expect(page.getByText('Atlas — dossier de test',{exact:true})).toHaveCount(0);
});
test('Collaborateur : affectations, refus hors dossier et vocabulaire métier',async({page})=>{
 await login(page,'staff');await expect(page.getByRole('heading',{name:'Mes dossiers'})).toBeVisible();
 await expect(page.locator('.dossier-card')).toHaveCount(1);
 await expect(page.locator('body')).not.toContainText('Sahara');
 await page.locator('.dossier-card').first().click();await expect(page).toHaveURL(/atlas\/overview$/);
 await expect(page.getByRole('heading',{name:'Vue d’ensemble',exact:true})).toBeVisible();
 await expect(page.locator('main')).not.toContainText(/\bIA\b|agent IA|assistant IA|score de confiance/i);
 await page.screenshot({path:'test-results/dossier-desktop.png',fullPage:true});
 const forbidden=await page.request.get('/api/dossiers/sahara/documents');expect(forbidden.status()).toBe(404);
});
test('Le dépôt client est persistant, isolé et sans accès aux travaux internes',async({page})=>{
 await login(page,'client');await page.getByRole('link',{name:'Mes documents',exact:true}).click();
 await page.locator('input[type=file]').setInputFiles({name:'piece-test.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4\n% browser test fixture\n%%EOF')});
 await expect(page.getByText('piece-test.pdf',{exact:true})).toBeVisible();await page.reload();
 await expect(page.getByText('piece-test.pdf',{exact:true})).toBeVisible();
 expect((await page.request.get('/api/dossiers/atlas/work')).status()).toBe(403);
 expect((await page.request.get('/api/knowledge/sources')).status()).toBe(403);
 await page.screenshot({path:'test-results/portail-client.png',fullPage:true});
});
test('Le référentiel reste visible sans prétendre contenir des lois validées',async({page})=>{
 await login(page,'manager');await page.goto('/cabinet/references');
 await expect(page.getByRole('heading',{name:'Référentiel réglementaire'})).toBeVisible();
 await expect(page.getByText('Bulletin officiel',{exact:true})).toBeVisible();
 await expect(page.locator('body')).toContainText('Aucun texte');
 await page.screenshot({path:'test-results/referentiel.png',fullPage:true});
});
