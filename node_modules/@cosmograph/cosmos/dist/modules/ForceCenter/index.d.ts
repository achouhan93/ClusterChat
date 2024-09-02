import { CoreModule } from "../core-module";
import { CosmosInputNode, CosmosInputLink } from "../../types";
export declare class ForceCenter<N extends CosmosInputNode, L extends CosmosInputLink> extends CoreModule<N, L> {
    private centermassFbo;
    private clearCentermassCommand;
    private calculateCentermassCommand;
    private runCommand;
    create(): void;
    initPrograms(): void;
    run(): void;
    destroy(): void;
}
